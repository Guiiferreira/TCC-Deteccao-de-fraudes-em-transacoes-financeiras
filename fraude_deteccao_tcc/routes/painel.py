"""
Painel web visual do sistema antifraude.

Diferente das rotas em routes/transacoes.py e routes/alertas.py (que
formam a API REST, autenticada por header X-API-Key para consumo por
outros sistemas), este painel é acessado pelo navegador e usa
autenticação por sessão: o analista informa a chave de acesso uma
vez, no login, e o Flask mantém a sessão autenticada via cookie.

Reaproveita as mesmas entidades (Transacao, ModeloTreinado) e a mesma
lógica de negócio das rotas de API, mas consulta o banco diretamente
em vez de fazer chamadas HTTP internas — mais simples e mais rápido
para um servidor renderizando suas próprias páginas.
"""

from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, current_app, flash, redirect, render_template,
    request, session, url_for,
)
from sqlalchemy import func

from models import db, Transacao, ModeloTreinado

painel_bp = Blueprint("painel", __name__, url_prefix="/painel")


def login_necessario(f):
    """
    Protege as rotas do painel atrás de autenticação por sessão
    (RNF02). Diferente do decorator @requer_autenticacao da API (que
    exige um header em cada requisição), aqui o analista autentica
    uma vez e a sessão do navegador mantém o acesso.
    """
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("painel_autenticado"):
            return redirect(url_for("painel.login"))
        return f(*args, **kwargs)
    return decorada


@painel_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        chave_informada = request.form.get("chave", "")
        if chave_informada == current_app.config["API_KEY"]:
            session["painel_autenticado"] = True
            return redirect(url_for("painel.alertas"))
        erro = "Chave de acesso inválida."
    return render_template("login.html", erro=erro)


@painel_bp.route("/logout")
def logout():
    session.pop("painel_autenticado", None)
    return redirect(url_for("painel.login"))


@painel_bp.route("/")
@login_necessario
def alertas():
    """
    Tela principal do painel (RF04): lista as transações com score
    acima do limiar configurável, ordenadas por score decrescente.
    """
    limiar = request.args.get(
        "min_score", type=float, default=current_app.config["LIMIAR_ALERTA_PADRAO"]
    )
    status = request.args.get("status")

    query = Transacao.query.filter(Transacao.score >= limiar)
    if status:
        query = query.filter(Transacao.status_revisao == status)

    lista = query.order_by(Transacao.score.desc()).all()

    return render_template("alertas.html", alertas=lista, limiar=limiar, status=status)


@painel_bp.route("/alertas/<int:transacao_id>/revisao", methods=["POST"])
@login_necessario
def revisar(transacao_id):
    """
    Ação de revisão manual do analista (RF05): marca um alerta como
    'fraude confirmada' ou 'falso positivo'.
    """
    novo_status = request.form.get("status_revisao")
    voltar_para = request.form.get("voltar_para") or url_for("painel.alertas")

    if novo_status not in ("fraude_confirmada", "falso_positivo"):
        flash("Status de revisão inválido.", "erro")
        return redirect(voltar_para)

    transacao = Transacao.query.get(transacao_id)
    if transacao is None:
        flash("Transação não encontrada.", "erro")
        return redirect(voltar_para)

    transacao.status_revisao = novo_status
    db.session.commit()

    # RNF04: log de auditoria também para revisões feitas pelo painel
    current_app.logger.info(
        "AUDITORIA: transacao_id=%s status_revisao alterado para '%s' via painel",
        transacao_id, novo_status,
    )

    rotulo = "fraude confirmada" if novo_status == "fraude_confirmada" else "falso positivo"
    flash(f"Transação #{transacao_id} marcada como {rotulo}.", "sucesso")
    return redirect(voltar_para)


@painel_bp.route("/transacoes")
@login_necessario
def transacoes():
    """
    Histórico completo de transações (RF07), com os mesmos filtros
    disponíveis na API: valor, status de revisão e intervalo de datas.
    """
    query = Transacao.query

    valor_min = request.args.get("valor_min", type=float)
    valor_max = request.args.get("valor_max", type=float)
    status_revisao = request.args.get("status_revisao")
    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")

    if valor_min is not None:
        query = query.filter(Transacao.valor >= valor_min)
    if valor_max is not None:
        query = query.filter(Transacao.valor <= valor_max)
    if status_revisao:
        query = query.filter(Transacao.status_revisao == status_revisao)

    if data_inicio_str:
        try:
            query = query.filter(Transacao.timestamp >= datetime.fromisoformat(data_inicio_str))
        except ValueError:
            flash("Data inicial inválida.", "erro")

    if data_fim_str:
        try:
            query = query.filter(Transacao.timestamp <= datetime.fromisoformat(data_fim_str))
        except ValueError:
            flash("Data final inválida.", "erro")

    lista = query.order_by(Transacao.timestamp.desc()).limit(500).all()

    return render_template("transacoes.html", transacoes=lista)


@painel_bp.route("/metricas")
@login_necessario
def metricas():
    """
    Dashboard de métricas do modelo ativo (RF06): precisão, recall,
    F1, matriz de confusão e volume de alertas por dia.
    """
    modelo_ativo = ModeloTreinado.query.filter_by(ativo=True).first()

    volume_por_dia = []
    volume_maximo = 1
    if modelo_ativo:
        limiar = current_app.config["LIMIAR_ALERTA_PADRAO"]
        resultado = (
            db.session.query(
                func.date(Transacao.timestamp).label("data"),
                func.count(Transacao.id).label("quantidade"),
            )
            .filter(Transacao.score >= limiar)
            .group_by(func.date(Transacao.timestamp))
            .order_by(func.date(Transacao.timestamp).desc())
            .limit(30)
            .all()
        )
        volume_por_dia = [(str(dia), qtd) for dia, qtd in resultado]
        if volume_por_dia:
            volume_maximo = max(qtd for _, qtd in volume_por_dia)

    return render_template(
        "metricas.html",
        modelo=modelo_ativo,
        volume_por_dia=volume_por_dia,
        volume_maximo=volume_maximo,
    )

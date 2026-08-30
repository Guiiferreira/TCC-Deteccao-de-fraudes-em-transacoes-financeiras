from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from models import db, Transacao
from services.auth import requer_autenticacao

alertas_bp = Blueprint("alertas", __name__)


@alertas_bp.route("/api/alertas", methods=["GET"])
@requer_autenticacao
def listar_alertas():
    """
    RF04: lista as transações com score acima de um limiar configurável
    (padrão 0.7) como "alerta", ordenadas por score decrescente.

    Query params opcionais: status, min_score
    """
    limiar = request.args.get(
        "min_score", type=float, default=current_app.config["LIMIAR_ALERTA_PADRAO"]
    )
    status = request.args.get("status")

    query = Transacao.query.filter(Transacao.score >= limiar)
    if status:
        query = query.filter(Transacao.status_revisao == status)

    alertas = query.order_by(Transacao.score.desc()).all()
    return jsonify([a.to_dict() for a in alertas])


@alertas_bp.route("/api/alertas/<int:transacao_id>/revisao", methods=["PATCH"])
@requer_autenticacao
def marcar_revisao(transacao_id):
    """
    RF05: permite que o analista marque um alerta como "fraude_confirmada"
    ou "falso_positivo". Esse feedback alimenta a tabela de transações e
    pode ser usado depois para reavaliar o modelo.
    """
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status_revisao")

    if novo_status not in ("fraude_confirmada", "falso_positivo"):
        return jsonify({
            "erro": "status_revisao deve ser 'fraude_confirmada' ou 'falso_positivo'."
        }), 400

    transacao = Transacao.query.get(transacao_id)
    if transacao is None:
        return jsonify({"erro": "Transação não encontrada."}), 404

    transacao.status_revisao = novo_status
    db.session.commit()

    # RNF04: log de auditoria — registra quem/quando alterou o status
    # de revisão, para fins de rastreabilidade. Usamos o logger padrão
    # do Flask/Python, que por padrão escreve no console/stderr; em
    # produção isso normalmente seria configurado para gravar em
    # arquivo ou serviço de log centralizado.
    current_app.logger.info(
        "AUDITORIA: transacao_id=%s status_revisao alterado para '%s'",
        transacao_id, novo_status,
    )

    return jsonify(transacao.to_dict())


@alertas_bp.route("/api/metricas", methods=["GET"])
@requer_autenticacao
def metricas_modelo():
    """
    RF06: exibe métricas do modelo (precisão, recall, F1, matriz de
    confusão) e volume de alertas por dia.
    """
    from models import ModeloTreinado

    modelo_ativo = ModeloTreinado.query.filter_by(ativo=True).first()
    if modelo_ativo is None:
        return jsonify({"erro": "Nenhum modelo ativo registrado no banco."}), 404

    limiar = current_app.config["LIMIAR_ALERTA_PADRAO"]

    # Volume de alertas por dia: agrupa as transações com score acima
    # do limiar por data (ignorando a hora), contando quantas caíram
    # em cada dia — útil para acompanhar tendência de alertas ao longo
    # do tempo (ex: gráfico no painel).
    volume_por_dia = (
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

    resposta = modelo_ativo.to_dict()
    resposta["volume_alertas_por_dia"] = [
        {"data": str(dia), "quantidade": quantidade}
        for dia, quantidade in volume_por_dia
    ]

    return jsonify(resposta)

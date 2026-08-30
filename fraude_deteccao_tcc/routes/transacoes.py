from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from models import db, Transacao
from services.ml_service import get_ml_service
from services.auth import requer_autenticacao

transacoes_bp = Blueprint("transacoes", __name__)


@transacoes_bp.route("/transacoes/classificar", methods=["POST"])
@requer_autenticacao
def classificar_transacao():
    """
    RF02: recebe os atributos de uma transação e retorna score de risco
    e classe prevista.
    RF03: armazena a transação classificada com score, classe e timestamp.
    RNF01: deve responder em menos de 500ms (o tempo é medido e devolvido
    na resposta, para que a equipe possa monitorar/registrar no artigo).
    """
    ml_service = get_ml_service()
    if ml_service is None or not ml_service.modelo_disponivel():
        return jsonify({
            "erro": "Nenhum modelo treinado disponível. Rode ml/train.py."
        }), 503

    dados = request.get_json(silent=True)
    if not dados or "features" not in dados or "valor" not in dados:
        return jsonify({
            "erro": "Corpo da requisição deve conter 'valor' e 'features' (dict)."
        }), 400

    resultado = ml_service.classificar(dados["features"])

    transacao = Transacao(
        valor=dados["valor"],
        features=dados["features"],
        score=resultado["score"],
        classe_prevista=resultado["classe_prevista"],
        versao_modelo=resultado["versao_modelo"],
    )
    db.session.add(transacao)
    db.session.commit()

    # RNF04: log de auditoria de toda classificação realizada
    current_app.logger.info(
        "AUDITORIA: transacao_id=%s classificada como '%s' (score=%.4f, modelo=%s)",
        transacao.id, resultado["classe_prevista"], resultado["score"],
        resultado["versao_modelo"],
    )

    return jsonify({
        "id": transacao.id,
        "score": resultado["score"],
        "classe_prevista": resultado["classe_prevista"],
        "tempo_resposta_ms": resultado["tempo_resposta_ms"],
        "versao_modelo": resultado["versao_modelo"],
        # RNF05: a classificação é probabilística e sujeita a falso
        # positivo/negativo — não substitui a análise humana final.
        "aviso": (
            "Esta classificação é uma estimativa probabilística gerada "
            "por modelo de Machine Learning, sujeita a falsos positivos "
            "e falsos negativos. Não substitui a análise humana final."
        ),
    }), 201


@transacoes_bp.route("/transacoes", methods=["GET"])
@requer_autenticacao
def listar_transacoes():
    """
    RF07: permite filtrar transações por intervalo de datas, valor
    mínimo/máximo e status de revisão.

    Query params aceitos (todos opcionais):
      data_inicio, data_fim (ISO 8601, ex: 2026-08-01 ou 2026-08-01T00:00:00)
      valor_min, valor_max, status_revisao
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
            data_inicio = datetime.fromisoformat(data_inicio_str)
            query = query.filter(Transacao.timestamp >= data_inicio)
        except ValueError:
            return jsonify({
                "erro": "data_inicio inválida. Use o formato ISO 8601 (ex: 2026-08-01 ou 2026-08-01T00:00:00)."
            }), 400

    if data_fim_str:
        try:
            data_fim = datetime.fromisoformat(data_fim_str)
            query = query.filter(Transacao.timestamp <= data_fim)
        except ValueError:
            return jsonify({
                "erro": "data_fim inválida. Use o formato ISO 8601 (ex: 2026-08-31 ou 2026-08-31T23:59:59)."
            }), 400

    transacoes = query.order_by(Transacao.timestamp.desc()).limit(500).all()
    return jsonify([t.to_dict() for t in transacoes])

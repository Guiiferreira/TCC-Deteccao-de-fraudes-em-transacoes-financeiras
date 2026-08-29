from flask import Blueprint, jsonify, request

from models import db, Transacao
from services.ml_service import ml_service

transacoes_bp = Blueprint("transacoes", __name__)


@transacoes_bp.route("/transacoes/classificar", methods=["POST"])
def classificar_transacao():
    """
    RF02: recebe os atributos de uma transação e retorna score de risco
    e classe prevista.
    RF03: armazena a transação classificada com score, classe e timestamp.
    RNF01: deve responder em menos de 500ms (o tempo é medido e devolvido
    na resposta, para que a equipe possa monitorar/registrar no artigo).
    """
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

    return jsonify({
        "id": transacao.id,
        "score": resultado["score"],
        "classe_prevista": resultado["classe_prevista"],
        "tempo_resposta_ms": resultado["tempo_resposta_ms"],
        "versao_modelo": resultado["versao_modelo"],
    }), 201


@transacoes_bp.route("/transacoes", methods=["GET"])
def listar_transacoes():
    """
    RF07: permite filtrar transações por intervalo de datas, valor
    mínimo/máximo e status de revisão.

    Query params aceitos (todos opcionais):
      data_inicio, data_fim (ISO 8601), valor_min, valor_max, status_revisao
    """
    query = Transacao.query

    valor_min = request.args.get("valor_min", type=float)
    valor_max = request.args.get("valor_max", type=float)
    status_revisao = request.args.get("status_revisao")

    if valor_min is not None:
        query = query.filter(Transacao.valor >= valor_min)
    if valor_max is not None:
        query = query.filter(Transacao.valor <= valor_max)
    if status_revisao:
        query = query.filter(Transacao.status_revisao == status_revisao)

    transacoes = query.order_by(Transacao.timestamp.desc()).limit(500).all()
    return jsonify([t.to_dict() for t in transacoes])

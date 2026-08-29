from flask import Blueprint, current_app, jsonify, request

from models import db, Transacao

alertas_bp = Blueprint("alertas", __name__)


@alertas_bp.route("/api/alertas", methods=["GET"])
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

    return jsonify(transacao.to_dict())


@alertas_bp.route("/api/metricas", methods=["GET"])
def metricas_modelo():
    """
    RF06: exibe métricas do modelo (precisão, recall, F1, matriz de
    confusão) e volume de alertas por dia.

    Nesta primeira versão do esqueleto, retorna as métricas registradas
    no treino (ver models/modelo_treinado.py) — a agregação de volume de
    alertas por dia será implementada quando o banco tiver dados reais.
    """
    from models import ModeloTreinado

    modelo_ativo = ModeloTreinado.query.filter_by(ativo=True).first()
    if modelo_ativo is None:
        return jsonify({"erro": "Nenhum modelo ativo registrado no banco."}), 404

    return jsonify(modelo_ativo.to_dict())

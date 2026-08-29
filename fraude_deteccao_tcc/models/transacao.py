from datetime import datetime, timezone

from models.database import db


class Transacao(db.Model):
    """
    Entidade Transacao — RF03: o sistema deve armazenar toda transação
    classificada com seu score, classe prevista e timestamp.

    O campo `features` guarda as variáveis de entrada usadas na
    classificação (ex.: as colunas V1..V28 + Amount do dataset Kaggle
    Credit Card Fraud) em formato JSON, para manter rastreabilidade de
    exatamente o que foi enviado ao modelo.
    """

    __tablename__ = "transacoes"

    id = db.Column(db.Integer, primary_key=True)

    # Dados de entrada da transação (mantidos como JSON para flexibilidade,
    # já que o dataset tem várias colunas numéricas: V1..V28, Amount etc.)
    valor = db.Column(db.Float, nullable=False)
    features = db.Column(db.JSON, nullable=False)

    # Resultado da classificação (RF02, RF03)
    score = db.Column(db.Float, nullable=False)  # 0 a 1 (probabilidade de fraude)
    classe_prevista = db.Column(db.String(20), nullable=False)  # "fraude" | "legitima"

    # RF05: marcação manual do analista após revisão do alerta
    status_revisao = db.Column(
        db.String(20), nullable=False, default="pendente"
    )  # "pendente" | "fraude_confirmada" | "falso_positivo"

    # Rastreabilidade (RF03, RNF04)
    timestamp = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    versao_modelo = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "valor": self.valor,
            "score": self.score,
            "classe_prevista": self.classe_prevista,
            "status_revisao": self.status_revisao,
            "timestamp": self.timestamp.isoformat(),
            "versao_modelo": self.versao_modelo,
        }

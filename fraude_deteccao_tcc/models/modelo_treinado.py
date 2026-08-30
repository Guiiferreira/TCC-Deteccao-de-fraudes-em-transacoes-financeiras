from datetime import datetime, timezone

from models.database import db


class ModeloTreinado(db.Model):
    """
    Entidade ModeloTreinado — registra cada versão de modelo treinado
    (RF01) e suas métricas de avaliação (RF06), permitindo comparar
    Regressão Logística, Árvore de Decisão e Random Forest entre si
    e ao longo do tempo (retreinamentos).
    """

    __tablename__ = "modelos_treinados"

    id = db.Column(db.Integer, primary_key=True)
    versao = db.Column(db.String(50), nullable=False, unique=True)
    algoritmo = db.Column(db.String(50), nullable=False)  # ex: "random_forest"
    data_treino = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Métricas de avaliação (RF06) — adequadas a cenário desbalanceado
    precisao = db.Column(db.Float, nullable=True)
    recall = db.Column(db.Float, nullable=True)
    f1_score = db.Column(db.Float, nullable=True)
    auc_roc = db.Column(db.Float, nullable=True)
    # Matriz de confusão salva como JSON: [[VN, FP], [FN, VP]]
    matriz_confusao = db.Column(db.JSON, nullable=True)

    # Caminho do arquivo .pkl serializado (RF01)
    caminho_arquivo = db.Column(db.String(255), nullable=False)

    # Marca qual modelo está ativo/em uso pela API neste momento
    ativo = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "versao": self.versao,
            "algoritmo": self.algoritmo,
            "data_treino": self.data_treino.isoformat(),
            "precisao": self.precisao,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "auc_roc": self.auc_roc,
            "matriz_confusao": self.matriz_confusao,
            "ativo": self.ativo,
        }

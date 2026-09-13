"""
Centraliza os imports do pacote models, para que o resto do código
possa escrever `from models import db, Transacao, ModeloTreinado`
diretamente, sem precisar conhecer em qual arquivo cada um está
definido (models/database.py, models/transacao.py, etc.).
"""

from models.database import db
from models.transacao import Transacao
from models.modelo_treinado import ModeloTreinado

__all__ = ["db", "Transacao", "ModeloTreinado"]

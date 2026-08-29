import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Configuração da aplicação.
    Em produção, essas variáveis devem vir de variáveis de ambiente
    (nunca deixar senha/segredo hardcoded no código).
    """

    # Banco de dados: por padrão usa SQLite local (fácil para desenvolvimento
    # e para a entrega do TCC). Para usar PostgreSQL, defina a variável de
    # ambiente DATABASE_URL, ex:
    # postgresql://usuario:senha@localhost:5432/fraude_deteccao
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'fraude_deteccao.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Caminho do modelo de ML treinado e serializado (gerado pelo ml/train.py)
    MODELO_PATH = os.path.join(BASE_DIR, "ml", "modelos_salvos", "modelo_atual.pkl")

    # Limiar de score (0 a 1) acima do qual uma transação vira "alerta" (RF04)
    LIMIAR_ALERTA_PADRAO = 0.7

    # Chave secreta da aplicação (usar variável de ambiente em produção)
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave-temporaria-trocar-em-producao")

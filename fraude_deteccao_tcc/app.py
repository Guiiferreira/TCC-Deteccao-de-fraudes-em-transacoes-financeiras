from flask import Flask, jsonify

from config import Config
from models import db
from services.ml_service import init_ml_service
from routes.transacoes import transacoes_bp
from routes.alertas import alertas_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Banco de dados
    db.init_app(app)
    with app.app_context():
        db.create_all()  # cria as tabelas se ainda não existirem

    # Serviço de ML (carrega o modelo treinado, se já existir)
    init_ml_service(app.config["MODELO_PATH"])

    # Registro das rotas (RF02, RF03, RF04, RF05, RF06, RF07)
    app.register_blueprint(transacoes_bp)
    app.register_blueprint(alertas_bp)

    @app.route("/")
    def health_check():
        return jsonify({
            "status": "ok",
            "servico": "API de Detecção de Fraude em Transações Financeiras",
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

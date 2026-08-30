"""
Script de teste manual da API — Parte 1 (esqueleto do projeto).

Insere transações e um modelo "simulados" no banco e testa todos os
endpoints que NÃO dependem do modelo de ML real (que só existirá após
a Parte 2 / ml/train.py). Serve para validar que a camada de API e o
banco de dados estão funcionando corretamente antes de plugar o
modelo de verdade.

Como rodar (no terminal, dentro da pasta do projeto):

    pip install -r requirements.txt
    python testar_local.py

Não precisa iniciar o servidor Flask (app.py) para rodar este script —
ele usa o "test_client" do próprio Flask, que simula as requisições
HTTP internamente, sem precisar de rede.
"""

from app import create_app
from models import db, Transacao, ModeloTreinado


def imprimir(titulo, resposta):
    print(f"\n=== {titulo} ===")
    print(f"Status: {resposta.status_code}")
    print(f"Corpo:  {resposta.get_json()}")


def main():
    app = create_app()
    client = app.test_client()

    # RNF02: as rotas agora exigem autenticação por API Key. Usa a
    # mesma chave padrão de desenvolvimento configurada em config.py
    # (troque via variável de ambiente API_KEY se tiver customizado).
    headers = {"X-API-Key": app.config["API_KEY"]}

    with app.app_context():
        # Simula um modelo já treinado (para testar /api/metricas antes
        # da Parte 2 existir de verdade)
        modelo = ModeloTreinado(
            versao="random_forest_v1_teste",
            algoritmo="random_forest",
            precisao=0.91,
            recall=0.76,
            f1_score=0.83,
            auc_roc=0.95,
            caminho_arquivo="ml/modelos_salvos/modelo_atual.pkl",
            ativo=True,
        )
        db.session.add(modelo)

        # Simula 3 transações já classificadas, como se o modelo tivesse
        # rodado sobre elas
        t1 = Transacao(
            valor=250.00, features={"V1": 0.2, "V2": -0.5},
            score=0.92, classe_prevista="fraude",
        )
        t2 = Transacao(
            valor=89.90, features={"V1": -0.1, "V2": 0.3},
            score=0.12, classe_prevista="legitima",
        )
        t3 = Transacao(
            valor=1500.00, features={"V1": 0.8, "V2": -1.2},
            score=0.81, classe_prevista="fraude",
        )
        db.session.add_all([t1, t2, t3])
        db.session.commit()
        print(f"Dados simulados inseridos: transações id={t1.id},{t2.id},{t3.id}")

    # --- Testes ---

    imprimir("GET /transacoes (lista todas)", client.get("/transacoes", headers=headers))

    imprimir(
        "GET /api/alertas (limiar padrão, score >= 0.7)",
        client.get("/api/alertas", headers=headers),
    )

    imprimir(
        "GET /api/alertas?min_score=0.9 (limiar customizado)",
        client.get("/api/alertas?min_score=0.9", headers=headers),
    )

    imprimir(
        "PATCH /api/alertas/1/revisao (marca como fraude confirmada)",
        client.patch(
            "/api/alertas/1/revisao", json={"status_revisao": "fraude_confirmada"},
            headers=headers,
        ),
    )

    imprimir(
        "GET /transacoes?status_revisao=fraude_confirmada (filtro por status)",
        client.get("/transacoes?status_revisao=fraude_confirmada", headers=headers),
    )

    imprimir(
        "GET /api/metricas (métricas do modelo ativo, com matriz de confusão e volume por dia)",
        client.get("/api/metricas", headers=headers),
    )

    imprimir(
        "GET /transacoes?valor_min=100&valor_max=1000 (filtro por valor)",
        client.get("/transacoes?valor_min=100&valor_max=1000", headers=headers),
    )

    imprimir(
        "GET /transacoes com filtro de data (RF07)",
        client.get(
            "/transacoes?data_inicio=2020-01-01&data_fim=2030-01-01", headers=headers
        ),
    )

    imprimir(
        "GET /api/alertas SEM autenticação (esperado: 401)",
        client.get("/api/alertas"),
    )

    # Este último ainda deve falhar (esperado) — só funciona após rodar
    # ml/train.py com o dataset real
    imprimir(
        "POST /transacoes/classificar (esperado: 503, modelo real ainda não existe)",
        client.post(
            "/transacoes/classificar",
            json={"valor": 150.0, "features": {"V1": 0.1}},
            headers=headers,
        ),
    )

    print("\nTodos os testes rodaram. Revise os status acima (200/201 = ok, "
          "401 no teste sem autenticação é esperado, 503 no último teste "
          "é esperado se o modelo real ainda não foi treinado).")


if __name__ == "__main__":
    main()

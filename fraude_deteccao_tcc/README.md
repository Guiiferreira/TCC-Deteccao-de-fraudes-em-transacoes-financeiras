# Sistema de Detecção de Fraude em Transações Financeiras

TCC — Tema 43 (catálogo do Prof. Nelson Aguiar).
Arquitetura: **Padrão C — Web/API + Serviço de ML**.

## Estrutura do projeto

```
fraude_deteccao_tcc/
├── app.py                  # Ponto de entrada da aplicação Flask
├── config.py                # Configurações (banco, caminho do modelo, limiar de alerta)
├── requirements.txt
├── models/                  # Entidades do banco de dados (SQLAlchemy)
│   ├── database.py           # Instância compartilhada do SQLAlchemy
│   ├── transacao.py           # Entidade Transacao (RF03)
│   └── modelo_treinado.py      # Entidade ModeloTreinado (RF01, RF06)
├── routes/                  # Endpoints da API
│   ├── transacoes.py         # POST /transacoes/classificar (RF02, RF03) + GET /transacoes (RF07)
│   └── alertas.py             # GET /api/alertas (RF04), PATCH revisão (RF05), GET /api/metricas (RF06)
├── services/
│   └── ml_service.py         # Carrega o modelo .pkl e faz a inferência (RNF01)
└── ml/
    ├── train.py               # Script de treino (a implementar na Parte 2)
    ├── dados/                  # Onde vai o dataset baixado (Kaggle Credit Card Fraud)
    └── modelos_salvos/          # Onde o modelo treinado (.pkl) é salvo
```

## Arquitetura escolhida

O sistema segue o **Padrão C — Web/API + Serviço de ML**: a lógica de
classificação fica isolada em `services/ml_service.py`, desacoplada da
camada web, e é exposta por uma API REST (Flask) com persistência em
banco de dados (`models/`). Essa separação permite treinar, avaliar e
trocar o algoritmo em uso (Regressão Logística, Árvore de Decisão ou
Random Forest) sem alterar as rotas da API, além de facilitar testes
automatizados da lógica de ML de forma independente da camada HTTP.

## Como rodar (quando o modelo já estiver treinado)

```bash
pip install -r requirements.txt
python app.py
```

A API sobe em `http://localhost:5000`. Endpoints disponíveis:

| Método | Rota | Requisito | Descrição |
|---|---|---|---|
| GET | `/` | — | Health check |
| POST | `/transacoes/classificar` | RF02, RF03 | Classifica uma transação e a salva |
| GET | `/transacoes` | RF07 | Lista transações com filtros |
| GET | `/api/alertas` | RF04 | Lista transações acima do limiar de risco |
| PATCH | `/api/alertas/<id>/revisao` | RF05 | Marca alerta como confirmado/falso positivo |
| GET | `/api/metricas` | RF06 | Métricas do modelo ativo |

## Próximos passos (Parte 2)

1. Baixar o dataset Kaggle Credit Card Fraud em `ml/dados/`
2. Implementar `ml/train.py`: análise exploratória, balanceamento de
   classes (SMOTE/undersampling/class_weight), treino dos 3 algoritmos,
   cálculo de métricas e serialização do modelo escolhido
3. Rodar `python ml/train.py` para gerar `ml/modelos_salvos/modelo_atual.pkl`
4. Testar o endpoint `/transacoes/classificar` com dados reais do dataset

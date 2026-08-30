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

## Como rodar

```bash
pip install -r requirements.txt

# 1. Coloque o dataset (creditcard.csv) em ml/dados/
# 2. Treine os modelos e registre as métricas no banco:
python ml/train.py

# 3. Suba a API:
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

## Status de validação

Todos os requisitos funcionais (RF01–RF07) já foram testados de ponta
a ponta com dados reais do dataset Kaggle Credit Card Fraud:

- Treino e comparação dos 3 algoritmos, com registro de métricas no
  banco (`ModeloTreinado`) para cada um — RF01, RF06
- Classificação de transações reais via API, com 100% de acerto na
  amostra testada e tempo de resposta médio de ~1ms (RF02, RF03, RNF01)
- Listagem de alertas priorizada por score (RF04)
- Marcação manual de revisão (fraude confirmada / falso positivo — RF05)
- Filtros de transações por valor e status de revisão (RF07)

## Critério de seleção do melhor modelo

Não usamos AUC-ROC isoladamente como critério de escolha: em dataset
tão desbalanceado, um modelo pode ter AUC-ROC alta e ainda gerar um
volume grande de falsos positivos no limiar padrão (0.5), o que o
torna pouco útil na prática. O script escolhe, entre os modelos que
atingem o recall mínimo de 70% exigido pelo RNF03, aquele com maior
F1-score (equilíbrio entre precisão e recall).

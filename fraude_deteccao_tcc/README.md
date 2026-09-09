# Sistema de Detecção de Fraude em Transações Financeiras

TCC — Tema 43 (catálogo do Prof. Nelson Aguiar).
Arquitetura: **Padrão C — Web/API + Serviço de ML**.

## Estrutura do projeto

```
fraude_deteccao_tcc/
├── app.py                  # Ponto de entrada da aplicação Flask
├── config.py                # Configurações (banco, caminho do modelo, limiar de alerta, API_KEY)
├── requirements.txt
├── models/                  # Entidades do banco de dados (SQLAlchemy)
│   ├── database.py           # Instância compartilhada do SQLAlchemy
│   ├── transacao.py           # Entidade Transacao (RF03)
│   └── modelo_treinado.py      # Entidade ModeloTreinado (RF01, RF06)
├── routes/                  # Endpoints da API
│   ├── transacoes.py         # POST /transacoes/classificar (RF02, RF03) + GET /transacoes (RF07)
│   ├── alertas.py             # GET /api/alertas (RF04), PATCH revisão (RF05), GET /api/metricas (RF06)
│   └── painel.py               # Painel web visual (mesmos RFs, para uso humano no navegador)
├── templates/                # Páginas HTML do painel (Jinja2)
├── static/
│   └── style.css              # Estilo do painel
├── services/
│   ├── ml_service.py         # Carrega o modelo .pkl e faz a inferência (RNF01)
│   └── auth.py                 # Autenticação por API Key, usada pela API (RNF02)
└── ml/
    ├── train.py               # Treina, compara e registra os 3 algoritmos
    ├── dados/                  # Onde vai o dataset baixado (Kaggle Credit Card Fraud)
    └── modelos_salvos/          # Onde o modelo treinado (.pkl) é salvo
```

## Arquitetura escolhida

O sistema segue o **Padrão C — Web/API + Serviço de ML**: a lógica de
classificação fica isolada em `services/ml_service.py`, desacoplada da
camada web, e é exposta tanto por uma API REST (para integração com
outros sistemas) quanto por um painel web (para uso humano), ambos
consumindo as mesmas entidades e regras de negócio. Essa separação
permite treinar, avaliar e trocar o algoritmo em uso (Regressão
Logística, Árvore de Decisão ou Random Forest) sem alterar as rotas,
além de facilitar testes automatizados da lógica de ML de forma
independente da camada HTTP.

## Como rodar

```bash
pip install -r requirements.txt

# 1. Coloque o dataset (creditcard.csv) em ml/dados/
# 2. Treine os modelos e registre as métricas no banco:
python ml/train.py

# 3. Suba a aplicação:
python app.py
```

A aplicação sobe em `http://localhost:5000`, com duas formas de acesso:

### Painel web (uso humano)

Acesse `http://localhost:5000/painel/login` no navegador e informe a
chave de acesso (definida em `config.py` / variável de ambiente
`API_KEY`). O painel tem três telas:

| Tela | Rota | Requisito |
|---|---|---|
| Alertas | `/painel/` | RF04 (listagem) + RF05 (ação de revisão) |
| Transações | `/painel/transacoes` | RF07 (filtros por valor, status e data) |
| Métricas do modelo | `/painel/metricas` | RF06 (precisão, recall, F1, matriz de confusão, volume por dia) |

### API REST (integração entre sistemas)

Endpoints autenticados por header `X-API-Key`:

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
a ponta com dados reais do dataset Kaggle Credit Card Fraud, tanto via
API (Postman) quanto via painel web (navegador real, com Playwright):

- Treino e comparação dos 3 algoritmos, com registro de métricas no
  banco (`ModeloTreinado`) para cada um — RF01, RF06
- Classificação de transações reais via API, com 100% de acerto na
  amostra testada e tempo de resposta médio de ~1ms (RF02, RF03, RNF01)
- Listagem de alertas priorizada por score, com filtro de limiar e
  status, na API e no painel — RF04
- Marcação manual de revisão (fraude confirmada / falso positivo),
  testada via clique real no painel — RF05
- Filtros de transações por valor, status e data, na API e no painel
  — RF07
- Autenticação obrigatória tanto na API (header) quanto no painel
  (sessão) — RNF02

## Critério de seleção do melhor modelo

Não usamos AUC-ROC isoladamente como critério de escolha: em dataset
tão desbalanceado, um modelo pode ter AUC-ROC alta e ainda gerar um
volume grande de falsos positivos no limiar padrão (0.5), o que o
torna pouco útil na prática. O script escolhe, entre os modelos que
atingem o recall mínimo de 70% exigido pelo RNF03, aquele com maior
F1-score (equilíbrio entre precisão e recall).

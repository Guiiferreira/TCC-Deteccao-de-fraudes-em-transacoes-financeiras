# Sistema de Detecção de Fraude em Transações Financeiras

TCC — Tema 43 (catálogo do Prof. Nelson Aguiar).
Arquitetura: **Padrão C — Web/API + Serviço de ML**.

## Estrutura do projeto

```
fraude_deteccao_tcc/
├── app.py                  # Ponto de entrada da aplicação Flask
├── config.py                # Configurações (banco, caminho do modelo, limiar de alerta, API_KEY)
├── requirements.txt
├── testar_local.py           # Script de teste automatizado dos principais endpoints
├── models/                  # Entidades do banco de dados (SQLAlchemy)
│   ├── database.py           # Instância compartilhada do SQLAlchemy
│   ├── transacao.py           # Entidade Transacao (RF03)
│   └── modelo_treinado.py      # Entidade ModeloTreinado (RF01, RF06)
├── routes/                  # Endpoints da API
│   ├── transacoes.py         # POST /transacoes/classificar (RF02, RF03) + GET /transacoes (RF07)
│   ├── alertas.py             # GET /api/alertas (RF04), PATCH revisão (RF05), GET /api/metricas (RF06)
│   └── painel.py               # Painel web visual (mesmas regras de negócio, acessado pelo navegador)
├── templates/                # Páginas HTML do painel (Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── alertas.html
│   ├── transacoes.html
│   └── metricas.html
├── static/
│   └── style.css              # Estilo do painel
├── services/
│   ├── ml_service.py         # Carrega o modelo .pkl e faz a inferência (RNF01)
│   └── auth.py                 # Autenticação por API Key, usada pela API (RNF02)
├── CHANGELOG.md               # Histórico de bugs encontrados e melhorias feitas
├── EVIDENCIAS_TESTES.md        # Registro dos testes manuais realizados via Postman/navegador
├── GLOSSARIO_CONCEITOS.md      # Explicação de score, limiar, classe prevista etc.
└── ml/
    ├── train.py               # Treina, compara e registra os 3 algoritmos
    ├── experimento.py         # Avaliação estatística: validação cruzada, McNemar, AUC-PR, balanceamento
    ├── medir_latencia_http.py # Mede o tempo de resposta da API rodando (RNF01)
    ├── resultados/            # Saída do experimento (CSVs, curva precisão x recall e RESULTADOS.md)
    ├── dados/                  # Onde vai o dataset baixado (Kaggle Credit Card Fraud) — não versionado
    └── modelos_salvos/          # Onde o modelo treinado (.pkl) é salvo — não versionado
```

## Arquitetura escolhida

O sistema segue o **Padrão C — Web/API + Serviço de ML**: a lógica de
classificação fica isolada em `services/ml_service.py`, desacoplada da
camada web, e é exposta tanto por uma API REST (para integração com
outros sistemas) quanto por um painel web, ambos
consumindo as mesmas entidades e regras de negócio. Essa separação
permite treinar, avaliar e trocar o algoritmo em uso (Regressão
Logística, Árvore de Decisão ou Random Forest) sem alterar as rotas,
além de facilitar testes automatizados da lógica de ML de forma
independente da camada HTTP.

## Como rodar

### 1. Pré-requisitos

- Python 3.11 ou superior instalado
- Git (para clonar o repositório)

### 2. Clonar o repositório e entrar na pasta do projeto

```bash
git clone https://github.com/Guiiferreira/TCC-Deteccao-de-fraudes-em-transacoes-financeiras.git
cd TCC-Deteccao-de-fraudes-em-transacoes-financeiras/fraude_deteccao_tcc
```

> **Atenção:** os comandos abaixo precisam ser rodados de dentro da pasta `fraude_deteccao_tcc` (a que contém o `app.py`), não da pasta raiz do repositório. Confira com `dir` (Windows) ou `ls` (Git Bash/Linux/Mac) se o `app.py` aparece na listagem antes de continuar.

### 3. Criar e ativar o ambiente virtual (venv)

```bash
python -m venv venv
```

**Ativar no PowerShell (Windows):**
```powershell
venv\Scripts\Activate.ps1
```
Se aparecer um erro de política de execução (`...não pode ser carregado porque a execução de scripts foi desabilitada...`), rode uma vez antes de ativar:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

**Ativar no Git Bash (Windows):**
```bash
source venv/Scripts/activate
```

**Ativar no Linux/Mac:**
```bash
source venv/bin/activate
```

Em todos os casos, o terminal deve passar a mostrar `(venv)` no início da linha — é assim que você confirma que o ambiente virtual está ativo antes de seguir.

### 4. Instalar as dependências

Com o `(venv)` ativo:
```bash
pip install -r requirements.txt
```
Pode demorar alguns minutos (scikit-learn e pandas são as mais pesadas).

### 5. Baixar o dataset

O dataset **não vai junto no repositório** (é grande demais para o Git). Baixe manualmente:

1. Acesse https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud (precisa de conta Kaggle gratuita)
2. Baixe e extraia o arquivo `creditcard.csv`
3. Coloque-o em `ml/dados/creditcard.csv`, dentro da pasta do projeto

### 6. Treinar os modelos

Com o dataset no lugar e o `(venv)` ativo:
```bash
python ml/train.py
```
Isso treina e compara os três algoritmos (Regressão Logística, Árvore de Decisão, Random Forest), escolhe o melhor modelo, salva-o em `ml/modelos_salvos/modelo_atual.pkl` e registra as métricas de todos os três no banco de dados.

#### Avaliação estatística dos modelos (opcional)

O `train.py` faz uma única divisão 70/30. Para repetir a avaliação completa usada no artigo (validação cruzada repetida, intervalos de confiança, teste de McNemar, AUC-PR, sensibilidade ao recall mínimo e comparação com SMOTE e undersampling):

```bash
python ml/experimento.py --configuracao-sistema   # hiperparâmetros usados pelo sistema
python ml/experimento.py                          # busca em grade de hiperparâmetros
```

Os resultados vão para `ml/resultados/sistema/` e `ml/resultados/ajustada/`, e o resumo de tudo está em `ml/resultados/RESULTADOS.md`. Os dois comandos são demorados: o primeiro leva cerca de 50 minutos num notebook comum, e o segundo, mais de uma hora. Como a semente é fixa (42), os números saem iguais em qualquer máquina, menos os de tempo.

Para medir o tempo de resposta da API, suba a aplicação (passo 7) e, em outro terminal, rode `python ml/medir_latencia_http.py`. O script envia 200 transações do conjunto de teste, e todas ficam gravadas no banco.

> Se você já tiver rodado o treino antes e mudar algo na estrutura do banco (ex: adicionar uma coluna em `models/`), pode ser necessário apagar o arquivo `fraude_deteccao.db` antes de rodar de novo, para que ele seja recriado do zero com o schema atualizado.

### 7. Rodar a aplicação

```bash
python app.py
```
A aplicação sobe em `http://localhost:5000`.

### 8. Acessar o sistema

**Painel web (pelo navegador):**
Acesse `http://localhost:5000/painel/login` e informe a chave de acesso configurada em `config.py` (variável `API_KEY`, padrão: `tcc-fraude-chave-2026`).

O painel tem três telas:

| Tela | Rota | Requisito |
|---|---|---|
| Alertas | `/painel/` | RF04 (listagem) + RF05 (ação de revisão) |
| Transações | `/painel/transacoes` | RF07 (filtros por valor, status e data) |
| Métricas do modelo | `/painel/metricas` | RF06 (precisão, recall, F1, matriz de confusão, volume por dia) |

**API REST (para testes com Postman, Insomnia ou outra ferramenta de API, ou para integração com outros sistemas):**

Todas as rotas exigem o header `X-API-Key` com o mesmo valor da chave de acesso.

| Método | Rota | Requisito | Descrição |
|---|---|---|---|
| GET | `/` | — | Health check |
| POST | `/transacoes/classificar` | RF02, RF03 | Classifica uma transação e a salva |
| GET | `/transacoes` | RF07 | Lista transações com filtros |
| GET | `/api/alertas` | RF04 | Lista transações acima do limiar de risco |
| PATCH | `/api/alertas/<id>/revisao` | RF05 | Marca alerta como confirmado/falso positivo |
| GET | `/api/metricas` | RF06 | Métricas do modelo ativo |

### 9. (Opcional) Rodar os testes automatizados

Com o `(venv)` ativo e a aplicação **parada** (o script sobe sua própria instância de teste):
```bash
python testar_local.py
```
Isso popula o banco com dados simulados e testa os principais endpoints da API, imprimindo o resultado de cada um no terminal.

## Simulando o Sistema Externo (para testes manuais)

O ator "Sistema Externo" (a plataforma de pagamento que, em um cenário
real, enviaria transações para classificação) não está integrado ao
projeto. Para testar o endpoint `POST /transacoes/classificar` de
forma realista — com casos reais e rótulo verdadeiro conhecido, em vez
de valores fictícios — extraia uma transação real do dataset com este
script:

```bash
python -c "
import pandas as pd
import json

df = pd.read_csv('ml/dados/creditcard.csv')
colunas = [c for c in df.columns if c != 'Class']

fraude = df[df['Class'] == 1].iloc[0]
legitima = df[df['Class'] == 0].iloc[0]

payload_fraude = {'valor': float(fraude['Amount']), 'features': {c: float(fraude[c]) for c in colunas}}
payload_legitima = {'valor': float(legitima['Amount']), 'features': {c: float(legitima[c]) for c in colunas}}

print('=== TRANSAÇÃO FRAUDULENTA (real) ===')
print(json.dumps(payload_fraude, indent=2))
print()
print('=== TRANSAÇÃO LEGÍTIMA (real) ===')
print(json.dumps(payload_legitima, indent=2))
"
```

Troque `.iloc[0]` por outro índice (`.iloc[1]`, `.iloc[2]`, etc.) para
pegar exemplos diferentes. Cole o JSON gerado no body de uma requisição
montada em uma ferramenta de teste de API — Postman, Insomnia, Thunder
Client (extensão do VSCode) ou até `curl` diretamente pelo terminal:

```
POST http://localhost:5000/transacoes/classificar
Header: X-API-Key: <sua chave de acesso>
Body (raw/JSON): (cole o JSON gerado)
```

Resultado esperado: a transação fraudulenta deve retornar
`classe_prevista: "fraude"` com score alto; a legítima deve retornar
`classe_prevista: "legitima"` com score baixo.

## Status de validação

Todos os requisitos funcionais (RF01–RF07) já foram testados de ponta
a ponta com dados reais do dataset Kaggle Credit Card Fraud, tanto via
API (Postman) quanto via painel web (navegador real, com Playwright):

- Treino e comparação dos 3 algoritmos, com registro de métricas no
  banco (`ModeloTreinado`) para cada um — RF01, RF06
- Classificação de transações reais via API, com 100% de acerto na
  amostra testada (RF02, RF03)
- Tempo de resposta medido em 200 requisições: média de 87 ms e 95%
  das requisições abaixo de 232 ms, num notebook Intel Core i5 de 2013
  (RNF01; detalhes em `ml/resultados/RESULTADOS.md`)
- Listagem de alertas priorizada por score, com filtro de limiar e
  status, na API e no painel — RF04
- Marcação manual de revisão (fraude confirmada / falso positivo),
  testada via clique real no painel — RF05
- Filtros de transações por valor, status e data, na API e no painel
  — RF07
- Autenticação obrigatória tanto na API (header) quanto no painel
  (sessão) — RNF02

Detalhes de cada teste realizado estão em `EVIDENCIAS_TESTES.md`, e o
histórico de bugs encontrados e corrigidos ao longo do desenvolvimento
está em `CHANGELOG.md`.

## Critério de seleção do melhor modelo

Não usamos AUC-ROC isoladamente como critério de escolha: em dataset
tão desbalanceado, um modelo pode ter AUC-ROC alta e ainda gerar um
volume grande de falsos positivos no limiar padrão (0.5), o que o
torna pouco útil na prática. O script escolhe, entre os modelos que
atingem o recall mínimo de 70% exigido pelo RNF03, aquele com maior
F1-score (equilíbrio entre precisão e recall).

Com os dados reais do dataset, isso faz o **Random Forest** ser
escolhido automaticamente (F1 ≈ 0,822, recall = 75,0%, precisão ≈
91,0%, AUC-PR ≈ 0,810), em vez da Regressão Logística — que tem a
maior AUC-ROC (≈ 0,968), mas gera 1.807 falsos positivos no conjunto
de teste.

O treino e a API usam a mesma regra de decisão: a transação é
classificada como fraude quando o score é maior ou igual a 0,5
(constante `LIMIAR_DECISAO` em `ml/train.py` e
`services/ml_service.py`). A validação estatística dessa escolha
(validação cruzada, teste de McNemar e sensibilidade a outros valores
de recall mínimo) está em `ml/resultados/RESULTADOS.md`.

## Documentação complementar

- `CHANGELOG.md` — bugs encontrados e melhorias feitas durante o
  desenvolvimento
- `EVIDENCIAS_TESTES.md` — testes manuais realizados via Postman e
  navegador, com resultados registrados
- `GLOSSARIO_CONCEITOS.md` — explicação de conceitos do sistema
  (score, limiar de alerta, classe prevista etc.)
- `ml/resultados/RESULTADOS.md` — resultados da avaliação estatística
  dos modelos e da medição de tempo de resposta

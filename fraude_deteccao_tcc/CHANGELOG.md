# Changelog — Sistema de Detecção de Fraude em Transações Financeiras

Registro de erros encontrados, correções e melhorias feitas durante o
desenvolvimento. Mantido para reaproveitar na Documentação de Software
e na seção de Metodologia/Discussão do artigo (mostra o processo de
desenvolvimento e validação, não só o resultado final).

## Etapa 1 — Esqueleto do projeto (API + entidades)

**Implementado:**
- Estrutura Padrão C (Web/API + Serviço de ML): `models/`, `routes/`,
  `services/`, `ml/`
- Entidades `Transacao` e `ModeloTreinado` (SQLAlchemy)
- Endpoints: `POST /transacoes/classificar`, `GET /transacoes`,
  `GET /api/alertas`, `PATCH /api/alertas/<id>/revisao`,
  `GET /api/metricas`

**Bug encontrado e corrigido:**
- A API não reconhecia o modelo de ML carregado mesmo depois de
  inicializado — causa: `from services.ml_service import ml_service`
  copia o valor da variável no momento do import (que era `None`
  antes da aplicação inicializar), então nunca era atualizado depois.
  Corrigido criando uma função `get_ml_service()` que sempre retorna o
  valor atual, em vez de importar a variável diretamente.

## Etapa 2 — Treino dos modelos (ml/train.py)

**Implementado:**
- Carregamento do dataset Kaggle Credit Card Fraud, análise
  exploratória, split estratificado treino/teste (70/30)
- Treino comparativo de 3 algoritmos: Regressão Logística, Árvore de
  Decisão, Random Forest — todos com `class_weight="balanced"` para
  tratar o desbalanceamento de classes
- Serialização do melhor modelo em `.pkl` (joblib)

**Bug/limitação encontrada e corrigida — critério de seleção do modelo:**
- Primeira versão escolhia o "melhor modelo" só pela métrica AUC-ROC.
  Resultado real: a Regressão Logística teve a maior AUC-ROC (0,968),
  mas gerou 1.807 falsos positivos em ~85 mil transações de teste —
  ou seja, estatisticamente "boa" no ranking geral, mas inutilizável
  na prática (sobrecarregaria a equipe de análise de alertas falsos).
- Corrigido: o critério passou a ser F1-score, considerado apenas
  entre os modelos que atingem o recall mínimo de 70% exigido pelo
  RNF03. Com dados reais, isso faz o Random Forest ser escolhido
  corretamente (F1=0,8165, recall=0,7365, precisão=0,9160).

**Melhoria — normalização da Regressão Logística:**
- A Regressão Logística não convergia (`ConvergenceWarning: lbfgs
  failed to converge`) por causa da diferença de escala entre as
  variáveis (ex: "Amount" varia de 0 a milhares, enquanto V1-V28 já
  estão em escala pequena).
- Corrigido envolvendo o modelo em um `Pipeline` com `StandardScaler`.
  Resultado: tempo de treino caiu de ~46s para ~2s, e o aviso de
  não-convergência desapareceu — tornando a comparação entre os 3
  algoritmos mais justa metodologicamente.

## Etapa 3 — Registro de métricas no banco + validação end-to-end

**Implementado:**
- Função `registrar_modelos_no_banco()`: grava as métricas dos 3
  algoritmos comparados na tabela `ModeloTreinado`, marcando o
  escolhido como ativo — alimenta o endpoint `GET /api/metricas`
- Validação end-to-end com dados reais do dataset via Postman:
  classificação de transações reais (100% de acerto na amostra
  testada), listagem de alertas, marcação manual de revisão, consulta
  de métricas — todos os fluxos confirmados funcionando

## Etapa 4 — Requisitos pendentes do escopo (RNF02, RNF04, RNF05, RF06, RF07)

**Implementado:**
- **RNF05**: toda resposta de classificação agora inclui aviso
  explícito de que é estimativa probabilística, sujeita a falsos
  positivos/negativos, e não substitui análise humana
- **RF06 (matriz de confusão)**: novo campo `matriz_confusao` na
  entidade `ModeloTreinado`, retornado em `/api/metricas`
- **RF06 (volume de alertas por dia)**: `/api/metricas` agora agrega e
  retorna a quantidade de alertas por dia (últimos 30 dias)
- **RF07 (filtro por data)**: `/transacoes` aceita `data_inicio` e
  `data_fim` (ISO 8601), com validação de formato (erro 400 se
  inválido)
- **RNF04 (log de auditoria)**: toda classificação e toda revisão
  manual geram uma linha de log via `current_app.logger`
- **RNF02 (autenticação)**: criado `services/auth.py` com decorator
  `@requer_autenticacao`, exigindo header `X-API-Key` em todas as
  rotas que expõem dados de transações; chave configurável via
  variável de ambiente `API_KEY`

**Validado via Postman com dados reais do dataset:**
- `GET /api/metricas` retornando corretamente matriz de confusão
  (`[[85285, 10], [39, 109]]`), todas as métricas do Random Forest e o
  campo `volume_alertas_por_dia`

**Erro encontrado (ambiente local, não é bug de código):**
- Ao rodar `ml/train.py` após adicionar o campo `matriz_confusao` na
  entidade `ModeloTreinado`, ocorreu erro
  `sqlite3.OperationalError: table modelos_treinados has no column
  named matriz_confusao`.
- Causa: o SQLAlchemy só cria tabelas que ainda não existem — não
  atualiza automaticamente tabelas já criadas quando o modelo Python
  muda (não há migração automática de schema). Como o arquivo
  `fraude_deteccao.db` já existia localmente (criado em execução
  anterior, antes desse campo existir), a tabela antiga ficou
  desatualizada em relação ao código novo.
- Solução: apagar o banco local (`fraude_deteccao.db`) e deixar a
  aplicação recriá-lo do zero na próxima execução. Em um cenário de
  produção real, isso seria tratado com uma ferramenta de migração de
  schema (ex: Flask-Migrate/Alembic) em vez de recriar o banco — vale
  citar essa limitação nas considerações finais do artigo, se for
  relevante.

## Pendências conhecidas (ainda não implementadas)

- Migração automática de schema (Flask-Migrate/Alembic) — hoje, mudanças no modelo exigem recriar o banco manualmente

## Etapa 5 — Painel web visual

**Implementado:**
- Blueprint `routes/painel.py` com autenticação por sessão (diferente
  da API, que usa header X-API-Key a cada requisição — aqui o
  analista informa a chave uma vez e o Flask mantém a sessão via
  cookie)
- Três telas: Alertas (RF04, com ação de revisão RF05 embutida),
  Transações (RF07, com filtros de valor/status/data) e Métricas do
  modelo (RF06, com matriz de confusão e volume por dia visualizados)
- Templates Jinja2 + CSS próprio (sem framework externo), com paleta
  navy e semântica de cor por nível de risco (vermelho/âmbar/verde)

**Bug encontrado e corrigido — barra de score invisível:**
- A barra de preenchimento do score (elemento visual que mostra o
  score como uma barra proporcional) não aparecia, mesmo com a cor de
  fundo correta aplicada via CSS (confirmado via inspeção do estilo
  computado).
- Causa: os elementos usados para a barra são `<span>`, que por
  padrão têm `display: inline` — e propriedades `width`/`height` não
  têm efeito em elementos inline, apenas em elementos block ou
  inline-block. O elemento "trilha" (track) escapava do problema por
  estar dentro de um container `display: flex` (que "blockifica"
  filhos diretos automaticamente), mas o elemento de "preenchimento"
  (fill), aninhado dentro do track, permanecia genuinamente inline.
- Corrigido adicionando `display: block` explicitamente à classe
  `.score-bar-fill` (e à barra equivalente do gráfico de volume por
  dia, que tinha o mesmo problema).
- Descoberto e corrigido via inspeção visual (captura de tela real do
  navegador) comparada ao estilo computado via DevTools — o valor de
  `background-color` computado already estava correto, o que
  descartou hipóteses de CSS não carregado e apontou para um problema
  de layout/exibição, não de cor.

**Validado via navegador (Playwright), com dados de teste variados:**
- Tela de Alertas: barra de score colorida por faixa de risco, filtro
  por limiar e status
- Ação de revisão: clique real no botão "Confirmar fraude" atualiza o
  status, mostra mensagem de sucesso e remove as ações da linha
- Tela de Transações: todas as 7 transações de teste listadas com
  badges de status coloridos
- Tela de Métricas: matriz de confusão com células coloridas por tipo
  (verdadeiro/falso positivo/negativo) e volume de alertas por dia
- Acesso sem login redireciona corretamente para a tela de
  autenticação (RNF02 também vale para o painel, não só para a API)

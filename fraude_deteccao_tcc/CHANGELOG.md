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
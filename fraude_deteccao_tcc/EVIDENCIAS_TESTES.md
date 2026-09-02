# Evidências de Testes da API

Registro dos testes manuais realizados via Postman contra a API, com
requisição e resultado obtido. Serve como evidência de validação
funcional para a Documentação de Software (seção de Testes/Validação)
e pode ser citado na Metodologia do artigo.

Ambiente: modelo ativo = Random Forest (F1=0,8165, recall=0,7365,
precisão=0,9160), treinado sobre o dataset Kaggle Credit Card Fraud
Detection (284.807 registros, 492 fraudes, 0,17%).

---

## Bloco 1 — Filtros de `GET /api/alertas`

### 1.1 — Listagem padrão (sem filtro de score)
**Requisição:**
```
GET http://localhost:5000/api/alertas
Header: X-API-Key: tcc-fraude-chave-2026
```
**Resultado:** `200 OK` — `[]` (lista vazia, pois o banco foi recriado do zero após a correção do schema e ainda não havia transações classificadas)

### 1.2 — Filtro por limiar de score elevado (min_score=0.95)
**Requisição:**
```
GET http://localhost:5000/api/alertas?min_score=0.95
```
**Resultado:** `200 OK` — `[]` (vazio, pois nenhuma transação
classificada até o momento atingiu score >= 0,95; a maior registrada
foi 0,85)

**Teste adicional — min_score=0.6 (para demonstrar o efeito do limiar):**
```
GET http://localhost:5000/api/alertas?min_score=0.6
```
**Resultado:** `200 OK` — retornou 3 transações (scores 0,85 / 0,69
/ 0,64), confirmando que transações com score entre 0,6 e 0,7 — que
não apareceriam com o limiar padrão de 0,7 — passam a ser listadas
quando o limiar é reduzido. Evidência prática do funcionamento do
parâmetro `min_score` (ver GLOSSARIO_CONCEITOS.md).

### 1.3 — Filtro por status de revisão
**Requisição:**
```
GET http://localhost:5000/api/alertas?status=pendente
```
**Resultado:** `200 OK` — retornou apenas 1 transação (id=7,
score=0,85). Importante: como esse endpoint usa o limiar padrão de
0,7 quando `min_score` não é informado, o filtro de status foi
aplicado somente sobre quem já havia passado nesse corte — as
transações de score 0,69 e 0,64 (vistas no teste com min_score=0.6)
não entraram na consulta, mesmo estando com status "pendente".

---

## Bloco 2 — Filtros de `GET /transacoes`

### 2.1 — Filtro por faixa de valor
**Requisição:**
```
GET http://localhost:5000/transacoes?valor_min=50&valor_max=100
```
**Resultado:** `200 OK` — retornou 2 transações dentro da faixa
(id=7, valor=59,0; id=2, valor=89,9), confirmando que o filtro
`valor_min`/`valor_max` funciona corretamente.

### 2.2 — Filtro por intervalo de datas
**Requisição:**
```
GET http://localhost:5000/transacoes?data_inicio=2026-08-30&data_fim=2026-08-31
```
**Resultado:** `200 OK` — retornou todas as transações classificadas
no dia do teste (30/08/2026), confirmando o funcionamento do filtro
de data (RF07).

### 2.3 — Filtros combinados (valor + status)
**Requisição:**
```
GET http://localhost:5000/transacoes?valor_min=0&status_revisao=pendente
```
**Resultado:** `200 OK` — retornou as transações com valor >= 0 e
status "pendente" (nenhuma havia sido revisada manualmente ainda),
confirmando que múltiplos filtros podem ser combinados na mesma
consulta.

---

## Bloco 3 — Validações e tratamento de erro

### 3.1 — Data em formato inválido (esperado: 400)
**Requisição:**
```
GET http://localhost:5000/transacoes?data_inicio=31/08/2026
```
**Resultado:** `400 Bad Request` — `{"erro": "data_inicio inválida.
Use o formato ISO 8601 (ex: 2026-08-01 ou 2026-08-01T00:00:00)."}`

### 3.2 — Requisição sem autenticação (esperado: 401)
**Requisição:**
```
GET http://localhost:5000/api/alertas
(sem o header X-API-Key)
```
**Resultado:** `401 Unauthorized` — `{"erro": "Não autenticado. Envie o header 'X-API-Key' com uma chave válida."}`

### 3.3 — Status de revisão inválido (esperado: 400)
**Requisição:**
```
PATCH http://localhost:5000/api/alertas/1/revisao
Body: { "status_revisao": "qualquer_coisa" }
```
**Resultado:** `400 Bad Request` — `{"erro": "status_revisao deve
ser 'fraude_confirmada' ou 'falso_positivo'."}`

### 3.4 — Transação inexistente (esperado: 404)
**Requisição:**
```
PATCH http://localhost:5000/api/alertas/99999/revisao
Body: { "status_revisao": "fraude_confirmada" }
```
**Resultado:** `404 Not Found` — `{"erro": "Transação não
encontrada."}`

---

## Testes complementares

### C.1 — Listagem sem nenhum filtro
**Requisição:**
```
GET http://localhost:5000/transacoes
Header: X-API-Key: tcc-fraude-chave-2026
```
**Resultado:** `200 OK` — retornou todas as transações classificadas
até o momento, ordenadas da mais recente para a mais antiga (confirma
o comportamento padrão de `GET /transacoes` sem parâmetros).

### C.2 — Filtro combinado min_score + status em /api/alertas
**Requisição:**
```
GET http://localhost:5000/api/alertas?min_score=0.6&status=pendente
```
**Resultado:** `200 OK` — retornou as 3 transações com score >= 0,6
E status "pendente" simultaneamente (id 7, 6 e 4), confirmando que os
dois filtros de `/api/alertas` podem ser combinados na mesma consulta.

### C.3 — Confirmação do log de auditoria (RNF04)
**Ação:** classificação de uma nova transação via `POST
/transacoes/classificar` (id=8, score=0,85, fraude).
**Resultado:** confirmado no terminal do servidor Flask:
```
[2026-09-02 17:43:08,559] INFO in transacoes: AUDITORIA: transacao_id=8
classificada como 'fraude' (score=0.8500, modelo=random_forest_v1_2026-08-30)
```
Evidencia que toda classificação realizada gera automaticamente uma
linha de log com identificação da transação, resultado e versão do
modelo utilizado, atendendo ao requisito de rastreabilidade (RNF04).

## Conclusão dos testes

Todos os 10 cenários testados (3 no Bloco 1, 3 no Bloco 2, 4 no Bloco
3) retornaram exatamente o comportamento esperado, cobrindo tanto os
"caminhos felizes" (filtros funcionando corretamente) quanto o
tratamento de erros (autenticação ausente, formato inválido, recurso
inexistente). Isso evidencia que os requisitos funcionais RF04, RF05,
RF06 e RF07, e os requisitos não funcionais RNF01, RNF02 e RNF05,
estão implementados e validados por meio de testes manuais reais
contra a API, com dados reais do dataset Kaggle Credit Card Fraud
Detection.

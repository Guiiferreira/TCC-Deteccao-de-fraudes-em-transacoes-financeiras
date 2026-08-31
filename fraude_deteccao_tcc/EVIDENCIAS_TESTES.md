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
**Resultado:** ✅ `200 OK` — `[]` (lista vazia, pois o banco foi recriado do zero após a correção do schema e ainda não havia transações classificadas)

### 1.2 — Filtro por limiar de score elevado (min_score=0.95)
**Requisição:**
```
GET http://localhost:5000/api/alertas?min_score=0.95
```
**Resultado:** _(a preencher)_
**Observação esperada:** deve retornar menos resultados que 1.1, já
que o filtro é mais restritivo.

**Teste adicional — min_score=0.6 (para demonstrar o efeito do limiar):**
```
GET http://localhost:5000/api/alertas?min_score=0.6
```
**Resultado:** ✅ `200 OK` — retornou 3 transações (scores 0,85 / 0,69
/ 0,64), confirmando que transações com score entre 0,6 e 0,7 — que
não apareceriam com o limiar padrão de 0,7 — passam a ser listadas
quando o limiar é reduzido. Evidência prática do funcionamento do
parâmetro `min_score` (ver GLOSSARIO_CONCEITOS.md).

### 1.3 — Filtro por status de revisão
**Requisição:**
```
GET http://localhost:5000/api/alertas?status=pendente
```
**Resultado:** _(a preencher)_

---

## Bloco 2 — Filtros de `GET /transacoes`

### 2.1 — Filtro por faixa de valor
**Requisição:**
```
GET http://localhost:5000/transacoes?valor_min=500&valor_max=2000
```
**Resultado:** _(a preencher)_

### 2.2 — Filtro por intervalo de datas
**Requisição:**
```
GET http://localhost:5000/transacoes?data_inicio=2026-08-01&data_fim=2026-08-31
```
**Resultado:** _(a preencher)_

### 2.3 — Filtros combinados (valor + status)
**Requisição:**
```
GET http://localhost:5000/transacoes?valor_min=100&status_revisao=pendente
```
**Resultado:** _(a preencher)_

---

## Bloco 3 — Validações e tratamento de erro

### 3.1 — Data em formato inválido (esperado: 400)
**Requisição:**
```
GET http://localhost:5000/transacoes?data_inicio=31/08/2026
```
**Resultado:** _(a preencher)_

### 3.2 — Requisição sem autenticação (esperado: 401)
**Requisição:**
```
GET http://localhost:5000/api/alertas
(sem o header X-API-Key)
```
**Resultado:** ✅ `401 Unauthorized` — `{"erro": "Não autenticado. Envie o header 'X-API-Key' com uma chave válida."}`

### 3.3 — Status de revisão inválido (esperado: 400)
**Requisição:**
```
PATCH http://localhost:5000/api/alertas/1/revisao
Body: { "status_revisao": "qualquer_coisa" }
```
**Resultado:** _(a preencher)_

### 3.4 — Transação inexistente (esperado: 404)
**Requisição:**
```
PATCH http://localhost:5000/api/alertas/99999/revisao
Body: { "status_revisao": "fraude_confirmada" }
```
**Resultado:** _(a preencher)_

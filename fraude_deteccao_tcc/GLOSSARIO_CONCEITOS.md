# Glossário de Conceitos — Sistema de Detecção de Fraude

Explicações de conceitos técnicos usados no sistema, registradas
durante o desenvolvimento para reaproveitar na Documentação de
Software (útil especialmente na seção que descreve a lógica de
negócio e no Referencial Teórico do artigo).

## Score de risco

Número entre 0 e 1, calculado pelo modelo de Machine Learning para
cada transação, representando a **probabilidade estimada** de que
aquela transação seja uma fraude. Não é uma resposta binária
("sim"/"não") — é uma medida de confiança:

- Score próximo de 0 → o modelo tem alta confiança de que é legítima
- Score próximo de 1 → o modelo tem alta confiança de que é fraude
- Score próximo de 0,5 → o modelo está "em dúvida"

## Classe prevista

Derivada do score através de um corte fixo em **0,5**: se
`score >= 0.5`, a classe prevista é "fraude"; caso contrário,
"legitima". Esse corte de 0,5 é diferente do "limiar de alerta"
(explicado abaixo) — são dois conceitos relacionados, mas não iguais.

## Limiar de alerta (threshold)

Ponto de corte **configurável** (padrão: 0,7) que define a partir de
qual score uma transação é considerada prioritária o suficiente para
aparecer na lista de alertas (`GET /api/alertas`), isto é, para
efetivamente chamar a atenção do analista humano.

Diferença importante em relação à "classe prevista": uma transação
pode ser classificada como "fraude" (score >= 0,5) e ainda **não**
aparecer como alerta, se seu score estiver abaixo do limiar
configurado (ex: score 0,69 é "fraude", mas não é alerta com o
limiar padrão de 0,7).

**Por que o limiar é maior que 0,5 e configurável:** é uma decisão de
negócio, um trade-off entre dois riscos:
- Limiar mais baixo → captura mais fraudes reais, mas gera mais
  falsos positivos (mais alertas para o analista revisar, muitos
  deles não sendo fraude de fato)
- Limiar mais alto → menos alertas falsos, mas corre o risco de
  deixar passar fraudes "moderadamente suspeitas"

O valor de 0,7 sugerido no escopo do tema é um ponto de partida, não
uma regra fixa — o parâmetro `min_score` da API permite ajustar esse
corte conforme a realidade de cada operação.

## Toda transação é salva, nem toda transação vira alerta

O endpoint `POST /transacoes/classificar` salva **todas** as
transações classificadas no banco de dados, independentemente do
score (é o que garante o histórico completo exigido pelo RF03/RNF04).
O filtro pelo limiar de 0,7 só é aplicado na **consulta**
`GET /api/alertas` — ou seja, o corte não decide o que é armazenado,
decide o que é **exibido como prioritário** para revisão.

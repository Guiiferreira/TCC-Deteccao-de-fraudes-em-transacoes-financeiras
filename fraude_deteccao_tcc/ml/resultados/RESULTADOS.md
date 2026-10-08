# Resultados do experimento — Grupo 06 (semente 42)

Base: 284.807 transações e 492 fraudes. Desenvolvimento (70%): 199.364 transações e 344 fraudes. Teste (30%): 85.443 transações e 148 fraudes. Mesma divisão do ml/train.py (train_test_split estratificado, random_state=42).

Regra de decisão: transação é fraude quando a probabilidade é ≥ 0,5, a mesma em services/ml_service.py e ml/train.py (constante LIMIAR_DECISAO). Antes da correção registrada na Etapa 6 do CHANGELOG, o train.py usava model.predict() (> 0,5) e registrava 109 VP e 10 FP para o Random Forest; com a regra da API, o mesmo modelo tem 111 VP e 11 FP.


# Parte A — Configuração do sistema (hiperparâmetros do ml/train.py)

Hiperparâmetros: Regressão Logística: C=1.0; Árvore de Decisão: padrão do scikit-learn; Random Forest: padrão do scikit-learn. Random Forest com 100 árvores; todos com class_weight="balanced"; StandardScaler só na Regressão Logística.

## CV repetida no desenvolvimento (5 × 3 = 15 dobras), limiar 0,5, média ± desvio

| Modelo | Precisão | Recall | F1 | AUC-ROC | AUC-PR |
|---|---|---|---|---|---|
| Regressão Logística | 0,070 ± 0,005 | 0,919 ± 0,023 | 0,131 ± 0,008 | 0,980 ± 0,007 | 0,763 ± 0,050 |
| Árvore de Decisão | 0,764 ± 0,054 | 0,710 ± 0,049 | 0,734 ± 0,035 | 0,855 ± 0,024 | 0,543 ± 0,052 |
| Random Forest | 0,913 ± 0,029 | 0,804 ± 0,041 | 0,854 ± 0,030 | 0,957 ± 0,013 | 0,847 ± 0,029 |

## Teste (30%), limiar 0,5, avaliação única

| Modelo | VP | FP | FN | Precisão | Recall [IC 95%] | F1 | AUC-ROC | AUC-PR |
|---|---|---|---|---|---|---|---|---|
| Regressão Logística | 130 | 1807 | 18 | 6,7% | 87,8% [81,6%; 92,2%] | 0,125 | 0,968 | 0,705 |
| Árvore de Decisão | 99 | 29 | 49 | 77,3% | 66,9% [59,0%; 74,0%] | 0,717 | 0,834 | 0,518 |
| Random Forest | 111 | 11 | 37 | 91,0% | 75,0% [67,5%; 81,3%] | 0,822 | 0,943 | 0,810 |

## AUC-PR no teste com IC 95% (bootstrap estratificado, 500 reamostragens)

| Item | Estimativa | IC 95% |
|---|---|---|
| AUC-PR LR | 0,705 | [0,623; 0,779] |
| AUC-PR DT | 0,518 | [0,440; 0,597] |
| AUC-PR RF | 0,810 | [0,741; 0,869] |
| AUC-PR RF − DT | 0,292 | [0,223; 0,355] |
| AUC-PR RF − LR | 0,105 | [0,048; 0,166] |
| AUC-PR LR − DT | 0,187 | [0,096; 0,268] |

## Teste de McNemar exato (limiar 0,5)

| Par (A × B) | Escopo | Só A acerta | Só B acerta | p |
|---|---|---|---|---|
| RF × DT | fraudes (recall) | 14 | 2 | 0,0042 |
| RF × DT | todas as transações | 38 | 8 | < 0,0001 |
| RF × LR | fraudes (recall) | 0 | 19 | < 0,0001 |
| RF × LR | todas as transações | 1796 | 19 | < 0,0001 |
| DT × LR | fraudes (recall) | 0 | 31 | < 0,0001 |
| DT × LR | todas as transações | 1792 | 45 | < 0,0001 |

## Mesmo recall: limiar escolhido no desenvolvimento, aplicado no teste

| Recall-alvo | Modelo | Limiar | VP | FP | Precisão | Recall no teste | F1 |
|---|---|---|---|---|---|---|---|
| 75,0% | Regressão Logística | 1,0000 | 108 | 17 | 86,4% | 73,0% | 0,791 |
| 75,0% | Árvore de Decisão | 0,0000 | 148 | 85295 | 0,2% | 100,0% | 0,003 |
| 75,0% | Random Forest | 0,6900 | 107 | 3 | 97,3% | 72,3% | 0,829 |
| 80,0% | Regressão Logística | 1,0000 | 116 | 30 | 79,5% | 78,4% | 0,789 |
| 80,0% | Árvore de Decisão | 0,0000 | 148 | 85295 | 0,2% | 100,0% | 0,003 |
| 80,0% | Random Forest | 0,5200 | 109 | 9 | 92,4% | 73,6% | 0,820 |
| 85,0% | Regressão Logística | 0,9824 | 122 | 90 | 57,5% | 82,4% | 0,678 |
| 85,0% | Árvore de Decisão | 0,0000 | 148 | 85295 | 0,2% | 100,0% | 0,003 |
| 85,0% | Random Forest | 0,1700 | 125 | 48 | 72,3% | 84,5% | 0,779 |

Quando o limiar cai para 0, o modelo não alcança aquele recall sem marcar todas as transações (acontece com a Árvore, cujas probabilidades são quase só 0 ou 1).

## Sensibilidade ao piso de recall (modelo escolhido pelo F1 no desenvolvimento; números do teste)

| Piso | Limiar 0,5 | Limiar ajustado: modelo (limiar) — precisão / recall / FP |
|---|---|---|
| 60,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 70,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 75,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 80,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,400) — 88,5% / 77,7% / 15 |
| 85,0% | Regressão Logística (6,7% / 87,8% / 1807) | Random Forest (0,170) — 72,3% / 84,5% / 48 |
| 90,0% | Regressão Logística (6,7% / 87,8% / 1807) | Regressão Logística (0,804) — 18,3% / 85,1% / 562 |

## Latência só do modelo (200 transações, uma por chamada, 1 núcleo)

| Modelo | Média (ms) | p95 (ms) | Máx. (ms) |
|---|---|---|---|
| Regressão Logística | 1,7 | 2,3 | 5,6 |
| Árvore de Decisão | 1,4 | 1,9 | 2,6 |
| Random Forest | 8,4 | 11,8 | 12,9 |

# Parte B — Configuração ajustada por busca em grade

Hiperparâmetros: Regressão Logística: C=10; Árvore de Decisão: max_depth=12, min_samples_leaf=50; Random Forest: max_depth=None, min_samples_leaf=1. Random Forest com 100 árvores; todos com class_weight="balanced"; StandardScaler só na Regressão Logística.

Grade (CV de 3 dobras no desenvolvimento, critério AUC-PR): LR C ∈ {0,001; 0,01; 0,1; 1; 10}; Árvore max_depth ∈ {4, 6, 8, 12, sem limite} × min_samples_leaf ∈ {1, 10, 50}; RF max_depth ∈ {10, sem limite} × min_samples_leaf ∈ {1, 5}.

## CV repetida no desenvolvimento (5 × 3 = 15 dobras), limiar 0,5, média ± desvio

| Modelo | Precisão | Recall | F1 | AUC-ROC | AUC-PR |
|---|---|---|---|---|---|
| Regressão Logística | 0,070 ± 0,004 | 0,918 ± 0,022 | 0,131 ± 0,008 | 0,980 ± 0,007 | 0,765 ± 0,049 |
| Árvore de Decisão | 0,175 ± 0,020 | 0,837 ± 0,036 | 0,289 ± 0,028 | 0,918 ± 0,018 | 0,747 ± 0,046 |
| Random Forest | 0,913 ± 0,029 | 0,804 ± 0,041 | 0,854 ± 0,030 | 0,957 ± 0,013 | 0,847 ± 0,029 |

## Teste (30%), limiar 0,5, avaliação única

| Modelo | VP | FP | FN | Precisão | Recall [IC 95%] | F1 | AUC-ROC | AUC-PR |
|---|---|---|---|---|---|---|---|---|
| Regressão Logística | 130 | 1803 | 18 | 6,7% | 87,8% [81,6%; 92,2%] | 0,125 | 0,968 | 0,705 |
| Árvore de Decisão | 119 | 523 | 29 | 18,5% | 80,4% [73,3%; 86,0%] | 0,301 | 0,901 | 0,724 |
| Random Forest | 111 | 11 | 37 | 91,0% | 75,0% [67,5%; 81,3%] | 0,822 | 0,943 | 0,810 |

## AUC-PR no teste com IC 95% (bootstrap estratificado, 500 reamostragens)

| Item | Estimativa | IC 95% |
|---|---|---|
| AUC-PR LR | 0,705 | [0,623; 0,779] |
| AUC-PR DT | 0,724 | [0,647; 0,791] |
| AUC-PR RF | 0,810 | [0,741; 0,869] |
| AUC-PR RF − DT | 0,086 | [0,045; 0,133] |
| AUC-PR RF − LR | 0,105 | [0,048; 0,166] |
| AUC-PR LR − DT | -0,019 | [-0,075; 0,038] |

## Teste de McNemar exato (limiar 0,5)

| Par (A × B) | Escopo | Só A acerta | Só B acerta | p |
|---|---|---|---|---|
| RF × DT | fraudes (recall) | 1 | 9 | 0,0215 |
| RF × DT | todas as transações | 514 | 10 | < 0,0001 |
| RF × LR | fraudes (recall) | 0 | 19 | < 0,0001 |
| RF × LR | todas as transações | 1792 | 19 | < 0,0001 |
| DT × LR | fraudes (recall) | 0 | 11 | 0,0010 |
| DT × LR | todas as transações | 1617 | 348 | < 0,0001 |

## Mesmo recall: limiar escolhido no desenvolvimento, aplicado no teste

| Recall-alvo | Modelo | Limiar | VP | FP | Precisão | Recall no teste | F1 |
|---|---|---|---|---|---|---|---|
| 75,0% | Regressão Logística | 1,0000 | 107 | 17 | 86,3% | 72,3% | 0,787 |
| 75,0% | Árvore de Decisão | 0,9987 | 108 | 21 | 83,7% | 73,0% | 0,780 |
| 75,0% | Random Forest | 0,6900 | 107 | 3 | 97,3% | 72,3% | 0,829 |
| 80,0% | Regressão Logística | 1,0000 | 116 | 30 | 79,5% | 78,4% | 0,789 |
| 80,0% | Árvore de Decisão | 0,9856 | 114 | 135 | 45,8% | 77,0% | 0,574 |
| 80,0% | Random Forest | 0,5200 | 109 | 9 | 92,4% | 73,6% | 0,820 |
| 85,0% | Regressão Logística | 0,9823 | 122 | 91 | 57,3% | 82,4% | 0,676 |
| 85,0% | Árvore de Decisão | 0,0000 | 148 | 85295 | 0,2% | 100,0% | 0,003 |
| 85,0% | Random Forest | 0,1700 | 125 | 48 | 72,3% | 84,5% | 0,779 |

Quando o limiar cai para 0, o modelo não alcança aquele recall sem marcar todas as transações (acontece com a Árvore, cujas probabilidades são quase só 0 ou 1).

## Sensibilidade ao piso de recall (modelo escolhido pelo F1 no desenvolvimento; números do teste)

| Piso | Limiar 0,5 | Limiar ajustado: modelo (limiar) — precisão / recall / FP |
|---|---|---|
| 60,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 70,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 75,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,540) — 94,8% / 73,6% / 6 |
| 80,0% | Random Forest (91,0% / 75,0% / 11) | Random Forest (0,400) — 88,5% / 77,7% / 15 |
| 85,0% | Regressão Logística (6,7% / 87,8% / 1803) | Random Forest (0,170) — 72,3% / 84,5% / 48 |
| 90,0% | Regressão Logística (6,7% / 87,8% / 1803) | Regressão Logística (0,803) — 18,2% / 85,1% / 566 |

## Latência só do modelo (200 transações, uma por chamada, 1 núcleo)

| Modelo | Média (ms) | p95 (ms) | Máx. (ms) |
|---|---|---|---|
| Regressão Logística | 1,5 | 1,9 | 3,1 |
| Árvore de Decisão | 1,3 | 1,7 | 3,8 |
| Random Forest | 8,2 | 11,7 | 15,0 |

# Parte C — Estratégias de balanceamento (configuração do sistema, CV de 5 dobras, limiar 0,5, reamostragem só no treino de cada dobra)

| Modelo | Estratégia | Precisão | Recall | F1 | FP por dobra | AUC-PR |
|---|---|---|---|---|---|---|
| Regressão Logística | ponderação de classes | 0,070 | 0,919 | 0,130 | 846 | 0,762 ± 0,058 |
| Regressão Logística | sem balanceamento | 0,874 | 0,645 | 0,742 | 6 | 0,781 ± 0,045 |
| Regressão Logística | undersampling | 0,054 | 0,924 | 0,101 | 1145 | 0,600 ± 0,183 |
| Regressão Logística | SMOTE | 0,066 | 0,921 | 0,124 | 897 | 0,761 ± 0,044 |
| Árvore de Decisão | ponderação de classes | 0,767 | 0,695 | 0,729 | 15 | 0,533 ± 0,017 |
| Árvore de Decisão | sem balanceamento | 0,718 | 0,744 | 0,729 | 20 | 0,534 ± 0,048 |
| Árvore de Decisão | undersampling | 0,016 | 0,930 | 0,032 | 3935 | 0,015 ± 0,002 |
| Árvore de Decisão | SMOTE | 0,459 | 0,785 | 0,578 | 64 | 0,360 ± 0,018 |
| Random Forest | ponderação de classes | 0,906 | 0,799 | 0,849 | 6 | 0,850 ± 0,017 |
| Random Forest | sem balanceamento | 0,932 | 0,794 | 0,857 | 4 | 0,849 ± 0,021 |
| Random Forest | undersampling | 0,064 | 0,910 | 0,119 | 959 | 0,766 ± 0,033 |
| Random Forest | SMOTE | 0,882 | 0,834 | 0,857 | 8 | 0,843 ± 0,021 |

A mesma comparação com a configuração ajustada está em ajustada/balanceamento_cv.csv; para o Random Forest os números são idênticos, porque a busca em grade escolheu os hiperparâmetros do sistema.

# Parte D — Latência de ponta a ponta na API (POST /transacoes/classificar, 200 requisições com transações do conjunto de teste)

Medida com ml/medir_latencia_http.py. Inclui autenticação, inferência, gravação no SQLite e log de auditoria. Ambiente principal: notebook Intel Core i5-3337U (1,8 GHz, 2 núcleos), 8 GB de RAM, Windows 11, servidor de desenvolvimento do Flask (python app.py, modo debug), modelo random_forest_v1.

| Configuração | Medida | Média (ms) | Mediana (ms) | p95 (ms) | Máx. (ms) |
|---|---|---|---|---|---|
| Antes (modelo com n_jobs=-1) | Ida e volta HTTP | 133,0 | 95,7 | 337,1 | 1.391,0 |
| Antes (modelo com n_jobs=-1) | Inferência no servidor | 97,9 | 74,3 | 170,1 | 1.046,7 |
| Depois (API com n_jobs=1) | Ida e volta HTTP | 87,1 | 61,9 | 232,4 | 525,2 |
| Depois (API com n_jobs=1) | Inferência no servidor | 47,7 | 39,5 | 98,8 | 345,2 |

O Random Forest é treinado com n_jobs=-1, e a API abria threads em todos os núcleos para classificar uma transação por vez. Com n_jobs=1 na API (services/ml_service.py) as previsões são as mesmas e o tempo médio caiu cerca de 35%; o p95 ficou em 232 ms, abaixo dos 500 ms do RNF01. O pior caso (525 ms) passou um pouco do limite, num notebook de 2013 rodando o servidor de desenvolvimento em modo debug, que não é o servidor indicado para produção.

Referência em outra máquina (Linux, 2 núcleos, servidor sem modo debug): antes 35,1 ms de média e 45,3 ms de p95; depois 14,9 ms de média, 19,0 ms de p95 e 32,1 ms de máximo.

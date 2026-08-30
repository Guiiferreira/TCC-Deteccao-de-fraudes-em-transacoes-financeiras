"""
Script de treino — Parte 2 do trabalho.

Carrega o dataset de fraude em cartão de crédito (Kaggle Credit Card
Fraud Detection), faz a análise exploratória básica, trata o
desbalanceamento de classes, treina e compara três algoritmos
(Regressão Logística, Árvore de Decisão e Random Forest), calcula as
métricas apropriadas para cenário desbalanceado e salva o melhor
modelo em ml/modelos_salvos/modelo_atual.pkl, pronto para ser usado
pela API (services/ml_service.py).

--------------------------------------------------------------------
COMO OBTER O DATASET (passo manual, feito uma única vez):
--------------------------------------------------------------------
1. Acesse: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
   (é necessário ter uma conta Kaggle gratuita e estar logado)
2. Clique em "Download" (arquivo .zip, ~150MB)
3. Extraia o arquivo "creditcard.csv" de dentro do zip
4. Coloque o creditcard.csv na pasta: ml/dados/creditcard.csv

Estrutura esperada do CSV: colunas "Time", "V1" a "V28", "Amount" e
"Class" (0 = transação legítima, 1 = fraude) — é exatamente o formato
padrão desse dataset no Kaggle.

--------------------------------------------------------------------
COMO RODAR:
--------------------------------------------------------------------
    python ml/train.py

O script imprime no terminal a análise exploratória, o comparativo de
métricas entre os três algoritmos, e ao final salva o modelo de melhor
F1-score entre os que atingem o recall mínimo de 70% (RNF03), pronto
para uso pela API.
"""

import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

# Adiciona a raiz do projeto ao path, para permitir rodar este script
# tanto de dentro da pasta ml/ quanto da raiz do projeto.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CAMINHO_DATASET = os.path.join(os.path.dirname(__file__), "dados", "creditcard.csv")
CAMINHO_MODELO_SAIDA = os.path.join(
    os.path.dirname(__file__), "modelos_salvos", "modelo_atual.pkl"
)


def carregar_dataset():
    """Carrega o CSV e valida se está no formato esperado."""
    if not os.path.exists(CAMINHO_DATASET):
        raise FileNotFoundError(
            f"\nDataset não encontrado em: {CAMINHO_DATASET}\n"
            "Baixe o dataset em https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud "
            "e coloque o arquivo 'creditcard.csv' na pasta ml/dados/ antes de rodar este script."
        )

    df = pd.read_csv(CAMINHO_DATASET)

    if "Class" not in df.columns:
        raise ValueError(
            "O CSV carregado não tem a coluna 'Class' — confira se o "
            "arquivo é realmente o dataset Kaggle Credit Card Fraud."
        )

    return df


def analise_exploratoria(df: pd.DataFrame):
    """Imprime estatísticas básicas — útil para citar no artigo."""
    total = len(df)
    fraudes = int(df["Class"].sum())
    legitimas = total - fraudes
    percentual_fraude = (fraudes / total) * 100

    print("=" * 60)
    print("ANÁLISE EXPLORATÓRIA DO DATASET")
    print("=" * 60)
    print(f"Total de registros:      {total:,}")
    print(f"Transações legítimas:    {legitimas:,} ({100 - percentual_fraude:.4f}%)")
    print(f"Transações fraudulentas: {fraudes:,} ({percentual_fraude:.4f}%)")
    print(f"Razão de desbalanceamento: 1 fraude para cada "
          f"{legitimas / fraudes:.0f} transações legítimas")
    print("=" * 60)
    print()

    return {
        "total": total,
        "fraudes": fraudes,
        "legitimas": legitimas,
        "percentual_fraude": percentual_fraude,
    }


def preparar_dados(df: pd.DataFrame):
    """
    Separa features (X) e alvo (y), e divide em treino/teste.

    Mantemos a divisão estratificada (stratify=y) para garantir que a
    proporção de fraudes seja preservada tanto no treino quanto no
    teste — importante justamente por causa do desbalanceamento.
    """
    colunas_features = [c for c in df.columns if c != "Class"]
    X = df[colunas_features]
    y = df["Class"]

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    return X_treino, X_teste, y_treino, y_teste, colunas_features


def treinar_e_avaliar(nome, modelo, X_treino, y_treino, X_teste, y_teste):
    """
    Treina um modelo e calcula as métricas adequadas a cenário
    desbalanceado (acurácia sozinha não é confiável aqui — um modelo
    que sempre prevê "não fraude" teria ~99,8% de acurácia e seria
    completamente inútil).
    """
    inicio = time.perf_counter()
    modelo.fit(X_treino, y_treino)
    tempo_treino = time.perf_counter() - inicio

    y_pred = modelo.predict(X_teste)
    y_proba = modelo.predict_proba(X_teste)[:, 1]

    metricas = {
        "algoritmo": nome,
        "precisao": precision_score(y_teste, y_pred, zero_division=0),
        "recall": recall_score(y_teste, y_pred, zero_division=0),
        "f1_score": f1_score(y_teste, y_pred, zero_division=0),
        "auc_roc": roc_auc_score(y_teste, y_proba),
        "tempo_treino_s": tempo_treino,
        "matriz_confusao": confusion_matrix(y_teste, y_pred).tolist(),
    }

    print(f"\n--- {nome} ---")
    print(f"Tempo de treino: {tempo_treino:.2f}s")
    print(f"Precisão:  {metricas['precisao']:.4f}")
    print(f"Recall:    {metricas['recall']:.4f}")
    print(f"F1-score:  {metricas['f1_score']:.4f}")
    print(f"AUC-ROC:   {metricas['auc_roc']:.4f}")
    print("Matriz de confusão:")
    print(f"  {metricas['matriz_confusao']}")
    print("\nRelatório detalhado:")
    print(classification_report(y_teste, y_pred, target_names=["legítima", "fraude"], zero_division=0))

    return modelo, metricas


def main():
    print("Carregando dataset...")
    df = carregar_dataset()

    analise_exploratoria(df)

    print("Dividindo dados em treino (70%) e teste (30%), de forma estratificada...")
    X_treino, X_teste, y_treino, y_teste, colunas_features = preparar_dados(df)
    print(f"Treino: {len(X_treino):,} registros | Teste: {len(X_teste):,} registros\n")

    # ------------------------------------------------------------------
    # Tratamento do desbalanceamento: usamos class_weight="balanced",
    # que ajusta o peso das classes durante o treino sem precisar
    # duplicar/sintetizar dados (abordagem mais simples e mais rápida
    # que SMOTE para uma primeira comparação; SMOTE pode ser testado
    # depois como uma variação adicional, se o grupo quiser aprofundar
    # a comparação metodológica no artigo).
    # ------------------------------------------------------------------

    modelos = {
        # Regressão Logística é sensível à escala das variáveis (ex.:
        # "Amount" varia de 0 a milhares, enquanto V1-V28 já estão em
        # escala pequena). Sem normalização, o otimizador pode não
        # convergir e o modelo fica prejudicado na comparação — por
        # isso ela vai dentro de um Pipeline com StandardScaler.
        # Árvore de Decisão e Random Forest não precisam disso: são
        # baseados em divisões (splits) por variável, não em distância
        # ou gradiente, então a escala não afeta o resultado.
        "Regressao_Logistica": Pipeline([
            ("normalizador", StandardScaler()),
            ("classificador", LogisticRegression(
                class_weight="balanced", max_iter=1000, random_state=42
            )),
        ]),
        "Arvore_de_Decisao": DecisionTreeClassifier(
            class_weight="balanced", random_state=42
        ),
        "Random_Forest": RandomForestClassifier(
            class_weight="balanced", n_estimators=100, random_state=42, n_jobs=-1
        ),
    }

    print("=" * 60)
    print("TREINANDO E COMPARANDO OS ALGORITMOS")
    print("=" * 60)

    resultados = []
    modelos_treinados = {}

    for nome, modelo in modelos.items():
        modelo_treinado, metricas = treinar_e_avaliar(
            nome, modelo, X_treino, y_treino, X_teste, y_teste
        )
        resultados.append(metricas)
        modelos_treinados[nome] = modelo_treinado

    # ------------------------------------------------------------------
    # Tabela comparativa final 
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("COMPARATIVO FINAL")
    print("=" * 60)
    tabela = pd.DataFrame(resultados)[
        ["algoritmo", "precisao", "recall", "f1_score", "auc_roc", "tempo_treino_s"]
    ]
    print(tabela.to_string(index=False))

    # ------------------------------------------------------------------
    # Escolha do melhor modelo.
    #
    # Não usamos AUC-ROC como critério único: em cenários muito
    # desbalanceados como este, um modelo pode ter AUC-ROC alta e ainda
    # assim gerar um volume enorme de falsos positivos no limiar padrão
    # (0.5) — o que o torna inútil na prática (sobrecarrega a equipe de
    # análise com alertas falsos).
    #
    # Critério adotado: entre os modelos que atendem ao RNF03 (recall
    # mínimo de 70% na classe fraude), escolhe o de maior F1-score, que
    # equilibra precisão e recall. Se nenhum atender ao RNF03, cai para
    # o de maior F1-score geral (e avisa explicitamente).
    # ------------------------------------------------------------------
    RECALL_MINIMO_RNF03 = 0.70

    candidatos = [r for r in resultados if r["recall"] >= RECALL_MINIMO_RNF03]

    if candidatos:
        melhor = max(candidatos, key=lambda r: r["f1_score"])
    else:
        melhor = max(resultados, key=lambda r: r["f1_score"])
        print(
            f"\nATENÇÃO: nenhum modelo atingiu o recall mínimo de "
            f"{RECALL_MINIMO_RNF03:.0%} exigido pelo RNF03. Selecionando "
            f"o de maior F1-score mesmo assim — revisar antes de usar em produção."
        )

    nome_melhor = melhor["algoritmo"]
    print(
        f"\nMelhor modelo (F1-score, entre os que atendem recall >= "
        f"{RECALL_MINIMO_RNF03:.0%}): {nome_melhor} "
        f"(F1={melhor['f1_score']:.4f}, recall={melhor['recall']:.4f}, "
        f"precisão={melhor['precisao']:.4f}, AUC-ROC={melhor['auc_roc']:.4f})"
    )

    # ------------------------------------------------------------------
    # Salva o melhor modelo no formato esperado por services/ml_service.py
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(CAMINHO_MODELO_SAIDA), exist_ok=True)

    versao = f"{nome_melhor.lower()}_v1_{pd.Timestamp.now().strftime('%Y-%m-%d')}"

    artefato = {
        "modelo": modelos_treinados[nome_melhor],
        "colunas": colunas_features,
        "versao": versao,
    }
    joblib.dump(artefato, CAMINHO_MODELO_SAIDA)

    print(f"\nModelo salvo em: {CAMINHO_MODELO_SAIDA}")
    print(f"Versão: {versao}")

    # ------------------------------------------------------------------
    # Registra os 3 modelos e suas métricas no banco (RF01, RF06),
    # marcando o escolhido como ativo — é o que o endpoint
    # GET /api/metricas consulta.
    # ------------------------------------------------------------------
    registrar_modelos_no_banco(resultados, nome_melhor, versao)

    print("\nPróximo passo: rode a API (python app.py) e teste o endpoint "
          "/transacoes/classificar com uma transação real do dataset.")

    return resultados, nome_melhor


def registrar_modelos_no_banco(resultados, nome_melhor, versao_melhor):
    """
    Insere um registro em ModeloTreinado para cada algoritmo comparado,
    marcando como ativo apenas o modelo escolhido (o mesmo que foi
    salvo em .pkl). Isso é o que alimenta o endpoint GET /api/metricas
    (RF06), permitindo consultar as métricas de qualquer um dos
    modelos comparados, não só o vencedor.

    Roda dentro do contexto da aplicação Flask para reaproveitar a
    mesma configuração de banco usada pela API (config.py).
    """
    # Import local para evitar dependência circular entre ml/train.py
    # e app.py fora da hora de rodar o treino.
    from app import create_app
    from models import db, ModeloTreinado

    app = create_app()
    with app.app_context():
        # Desativa qualquer modelo anteriormente marcado como ativo
        ModeloTreinado.query.update({"ativo": False})

        for r in resultados:
            eh_o_escolhido = r["algoritmo"] == nome_melhor
            registro = ModeloTreinado(
                versao=versao_melhor if eh_o_escolhido else f"{r['algoritmo'].lower()}_{pd.Timestamp.now().strftime('%Y-%m-%d_%H%M%S')}",
                algoritmo=r["algoritmo"],
                precisao=r["precisao"],
                recall=r["recall"],
                f1_score=r["f1_score"],
                auc_roc=r["auc_roc"],
                caminho_arquivo=CAMINHO_MODELO_SAIDA if eh_o_escolhido else "não salvo (não foi o modelo escolhido)",
                ativo=eh_o_escolhido,
            )
            db.session.add(registro)

        db.session.commit()

    print(f"\n{len(resultados)} modelo(s) registrado(s) no banco de dados "
          f"(tabela modelos_treinados). Modelo ativo: {nome_melhor}.")


if __name__ == "__main__":
    main()

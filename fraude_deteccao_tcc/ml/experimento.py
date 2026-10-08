"""
Experimento de avaliação dos classificadores de fraude (Grupo 06, Tema 43).

Responde aos itens 1 a 6 do feedback de 08/10/2026:
  1. validação cruzada estratificada repetida, com média, desvio e semente informada;
     conjunto de teste separado, usado apenas na avaliação final;
  2. intervalo de confiança (Wilson e bootstrap) e teste de McNemar pareado;
  3. hiperparâmetros escolhidos por validação cruzada e limiar de decisão ajustado,
     com comparação dos modelos para o mesmo recall e curva precisão x recall;
  4. AUC-PR (average precision);
  5. sensibilidade da escolha do modelo ao piso de recall;
  6. comparação de ponderação de classes, nenhum balanceamento, undersampling e SMOTE,
     e latência de inferência por requisição.

Protocolo
  - Separação 70/30 estratificada (semente 42). O teste só entra na avaliação final.
  - Tudo que é escolha (hiperparâmetros, limiar, modelo) usa apenas os 70% de desenvolvimento.
  - Limiares são escolhidos sobre as previsões fora da dobra (out-of-fold) da CV repetida.

Uso (na raiz do projeto, com o creditcard.csv em ml/dados/):
  python ml/experimento.py --configuracao-sistema   # hiperparâmetros do ml/train.py
  python ml/experimento.py                          # busca em grade + SMOTE/undersampling
Os resultados (CSVs e curva precisão x recall) vão para ml/resultados/sistema/
ou ml/resultados/ajustada/. A versão com busca em grade é a mais demorada.
"""
import argparse
import json
import os
import time
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from scipy.stats import binomtest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, precision_recall_curve,
                             roc_auc_score)
from sklearn.model_selection import (ParameterGrid, RepeatedStratifiedKFold,
                                     StratifiedKFold, train_test_split)
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")

SEED = 42
N_SPLITS, N_REPEATS = 5, 3
FLOORS = [0.60, 0.70, 0.75, 0.80, 0.85, 0.90]
MATCHED_RECALLS = [0.75, 0.80, 0.85]
NOMES = {"LR": "Regressão Logística", "DT": "Árvore de Decisão", "RF": "Random Forest"}


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---------------------------------------------------------------- modelos
def make_model(nome, params=None, sampler=None, class_weight="balanced"):
    params = dict(params or {})
    if nome == "LR":
        clf = LogisticRegression(class_weight=class_weight, max_iter=2000,
                                 random_state=SEED, **params)
        steps = [("scaler", StandardScaler())]
    elif nome == "DT":
        clf = DecisionTreeClassifier(class_weight=class_weight, random_state=SEED, **params)
        steps = []
    else:
        clf = RandomForestClassifier(class_weight=class_weight, random_state=SEED,
                                     n_jobs=2, n_estimators=100, **params)
        steps = []
    if sampler is not None:
        steps.append(("sampler", sampler))
    steps.append(("clf", clf))
    return ImbPipeline(steps)


GRADES = {
    "LR": {"C": [0.001, 0.01, 0.1, 1, 10]},
    "DT": {"max_depth": [4, 6, 8, 12, None], "min_samples_leaf": [1, 10, 50]},
    "RF": {"max_depth": [10, None], "min_samples_leaf": [1, 5]},
}


# ---------------------------------------------------------------- métricas
def conf(y, p, thr):
    pred = p >= thr
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precisao=prec, recall=rec, f1=f1)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def thr_piso(y, p, piso):
    """Limiar que maximiza F1 sujeito a recall >= piso (em y, p fornecidos)."""
    pr, rc, th = precision_recall_curve(y, p)
    pr, rc = pr[:-1], rc[:-1]
    ok = rc >= piso
    if not ok.any():
        return None
    f1 = np.where(pr + rc > 0, 2 * pr * rc / (pr + rc + 1e-12), 0)
    f1 = np.where(ok, f1, -1)
    return float(th[int(np.argmax(f1))])


def thr_recall(y, p, alvo):
    """Maior limiar cujo recall em (y, p) ainda atinge o alvo."""
    pr, rc, th = precision_recall_curve(y, p)
    rc = rc[:-1]
    ok = np.where(rc >= alvo)[0]
    return float(th[ok.max()]) if len(ok) else None


# ---------------------------------------------------------------- etapas
def tuning(Xdev, ydev, out):
    log("Hiperparâmetros: busca em grade, CV estratificada de 3 dobras, critério AUC-PR")
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    linhas, melhores = [], {}
    for nome, grade in GRADES.items():
        for params in ParameterGrid(grade):
            aps = []
            for tr, va in skf.split(Xdev, ydev):
                m = make_model(nome, params).fit(Xdev.iloc[tr], ydev.iloc[tr])
                aps.append(average_precision_score(ydev.iloc[va], m.predict_proba(Xdev.iloc[va])[:, 1]))
            linhas.append(dict(modelo=nome, **{k: str(v) for k, v in params.items()},
                               auc_pr_media=np.mean(aps), auc_pr_dp=np.std(aps, ddof=1)))
            log(f"  {nome} {params} AUC-PR={np.mean(aps):.4f}")
        sub = [l for l in linhas if l["modelo"] == nome]
        melhor = max(sub, key=lambda l: l["auc_pr_media"])
        melhores[nome] = {k: _parse(v) for k, v in melhor.items()
                          if k not in ("modelo", "auc_pr_media", "auc_pr_dp")}
    pd.DataFrame(linhas).to_csv(os.path.join(out, "hiperparametros_busca.csv"), index=False)
    return melhores


def _parse(v):
    if v == "None":
        return None
    try:
        return int(v)
    except ValueError:
        return float(v)


def cv_repetida(melhores, Xdev, ydev, out):
    log(f"CV repetida: {N_SPLITS} dobras x {N_REPEATS} repetições, semente {SEED}")
    rskf = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=SEED)
    folds = list(rskf.split(Xdev, ydev))
    linhas, oof = [], {n: [] for n in melhores}
    for nome, params in melhores.items():
        for i, (tr, va) in enumerate(folds):
            m = make_model(nome, params).fit(Xdev.iloc[tr], ydev.iloc[tr])
            p = m.predict_proba(Xdev.iloc[va])[:, 1]
            yv = ydev.iloc[va].values
            c = conf(yv, p, 0.5)
            linhas.append(dict(modelo=nome, repeticao=i // N_SPLITS, dobra=i % N_SPLITS,
                               precisao=c["precisao"], recall=c["recall"], f1=c["f1"],
                               auc_roc=roc_auc_score(yv, p), auc_pr=average_precision_score(yv, p)))
            oof[nome].append((yv, p))
        log(f"  {nome} concluído")
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(out, "cv_por_dobra.csv"), index=False)
    resumo = df.groupby("modelo")[["precisao", "recall", "f1", "auc_roc", "auc_pr"]].agg(["mean", "std"])
    resumo.columns = [f"{a}_{b}" for a, b in resumo.columns]
    resumo.to_csv(os.path.join(out, "cv_resumo.csv"))
    oof_y = {n: np.concatenate([a for a, _ in v]) for n, v in oof.items()}
    oof_p = {n: np.concatenate([b for _, b in v]) for n, v in oof.items()}
    return df, oof_y, oof_p


def avaliacao_final(melhores, Xdev, ydev, Xte, yte, oof_y, oof_p, out):
    log("Ajuste final no desenvolvimento e avaliação única no teste")
    modelos, ptest = {}, {}
    for nome, params in melhores.items():
        modelos[nome] = make_model(nome, params).fit(Xdev, ydev)
        ptest[nome] = modelos[nome].predict_proba(Xte)[:, 1]
    y = yte.values

    # Tabela 1 revisada: limiar padrão 0,5
    t1 = []
    for n, p in ptest.items():
        c = conf(y, p, 0.5)
        lo, hi = wilson(c["tp"], c["tp"] + c["fn"])
        plo, phi = wilson(c["tp"], c["tp"] + c["fp"])
        t1.append(dict(modelo=n, limiar=0.5, **c, recall_ic_inf=lo, recall_ic_sup=hi,
                       precisao_ic_inf=plo, precisao_ic_sup=phi,
                       auc_roc=roc_auc_score(y, p), auc_pr=average_precision_score(y, p)))
    t1 = pd.DataFrame(t1)
    t1.to_csv(os.path.join(out, "teste_limiar_0_5.csv"), index=False)

    # Mesmo recall (limiar escolhido no OOF do desenvolvimento)
    t2 = []
    for alvo in MATCHED_RECALLS:
        for n, p in ptest.items():
            thr = thr_recall(oof_y[n], oof_p[n], alvo)
            c = conf(y, p, thr)
            t2.append(dict(recall_alvo=alvo, modelo=n, limiar=thr, **c))
    t2 = pd.DataFrame(t2)
    t2.to_csv(os.path.join(out, "teste_mesmo_recall.csv"), index=False)

    # Sensibilidade ao piso de recall
    sens = []
    for regime in ("limiar_0_5", "limiar_ajustado"):
        for piso in FLOORS:
            cand = []
            for n, p in ptest.items():
                if regime == "limiar_0_5":
                    thr = 0.5
                else:
                    thr = thr_piso(oof_y[n], oof_p[n], piso)
                if thr is None:
                    cand.append(dict(modelo=n, viavel=False))
                    continue
                co = conf(oof_y[n], oof_p[n], thr)  # decisão só com o desenvolvimento
                ct = conf(y, p, thr)
                cand.append(dict(modelo=n, viavel=co["recall"] >= piso, limiar=thr,
                                 oof_recall=co["recall"], oof_f1=co["f1"],
                                 teste_precisao=ct["precisao"], teste_recall=ct["recall"],
                                 teste_f1=ct["f1"], teste_fp=ct["fp"], teste_tp=ct["tp"]))
            viaveis = [c for c in cand if c.get("viavel")]
            escolhido = max(viaveis, key=lambda c: c["oof_f1"])["modelo"] if viaveis else None
            for c in cand:
                sens.append(dict(regime=regime, piso=piso, escolhido=(c["modelo"] == escolhido), **c))
    sens = pd.DataFrame(sens)
    sens.to_csv(os.path.join(out, "sensibilidade_piso.csv"), index=False)

    # McNemar exato (pareado) sobre as previsões em 0,5
    pred = {n: (p >= 0.5).astype(int) for n, p in ptest.items()}
    mc = []
    for a, b in [("RF", "DT"), ("RF", "LR"), ("DT", "LR")]:
        for escopo, mask in (("fraudes (recall)", y == 1), ("todas as transações", np.ones_like(y, bool))):
            ok_a = (pred[a][mask] == y[mask])
            ok_b = (pred[b][mask] == y[mask])
            n10 = int((ok_a & ~ok_b).sum())
            n01 = int((~ok_a & ok_b).sum())
            pv = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
            mc.append(dict(par=f"{a} x {b}", escopo=escopo, so_a_acerta=n10, so_b_acerta=n01, p_valor=pv))
    mc = pd.DataFrame(mc)
    mc.to_csv(os.path.join(out, "mcnemar.csv"), index=False)

    # Bootstrap estratificado de AUC-PR (IC 95% e diferenças pareadas)
    rng = np.random.default_rng(SEED)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    B = 500
    aps = {n: [] for n in ptest}
    for _ in range(B):
        idx = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        for n, p in ptest.items():
            aps[n].append(average_precision_score(y[idx], p[idx]))
    bt = []
    for n in aps:
        a = np.array(aps[n])
        bt.append(dict(item=f"AUC-PR {n}", estimativa=average_precision_score(y, ptest[n]),
                       ic_inf=np.percentile(a, 2.5), ic_sup=np.percentile(a, 97.5)))
    for a_, b_ in [("RF", "DT"), ("RF", "LR"), ("LR", "DT")]:
        d = np.array(aps[a_]) - np.array(aps[b_])
        bt.append(dict(item=f"AUC-PR {a_} − {b_}",
                       estimativa=average_precision_score(y, ptest[a_]) - average_precision_score(y, ptest[b_]),
                       ic_inf=np.percentile(d, 2.5), ic_sup=np.percentile(d, 97.5)))
    pd.DataFrame(bt).to_csv(os.path.join(out, "bootstrap_auc_pr.csv"), index=False)

    # Curva precisão x recall
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=160)
    for n, p in ptest.items():
        pr, rc, _ = precision_recall_curve(y, p)
        ax.plot(rc, pr, label=f"{NOMES[n]} (AUC-PR = {average_precision_score(y, p):.3f})")
        c = conf(y, p, 0.5)
        ax.scatter([c["recall"]], [c["precisao"]], s=28, zorder=3)
    ax.axhline(y.mean(), ls=":", color="gray", lw=1)
    ax.set_xlabel("Recall"); ax.set_ylabel("Precisão"); ax.set_ylim(0, 1.02); ax.set_xlim(0, 1.0)
    ax.legend(loc="lower left", fontsize=8); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(os.path.join(out, "curva_precisao_recall.png")); plt.close(fig)

    # Latência de inferência (uma transação por chamada, sem rede nem banco)
    lat = []
    rs = np.random.default_rng(SEED)
    idxs = rs.choice(len(Xte), 200, replace=False)
    for n, m in modelos.items():
        if n == "RF":
            m.set_params(clf__n_jobs=1)
        for i in idxs[:10]:
            m.predict_proba(Xte.iloc[[i]])
        t = []
        for i in idxs:
            t0 = time.perf_counter(); m.predict_proba(Xte.iloc[[i]]); t.append((time.perf_counter() - t0) * 1000)
        lat.append(dict(modelo=n, requisicoes=len(t), media_ms=np.mean(t), p95_ms=np.percentile(t, 95), max_ms=np.max(t)))
    pd.DataFrame(lat).to_csv(os.path.join(out, "latencia_inferencia.csv"), index=False)
    return t1, t2, sens, mc


def balanceamento(melhores, Xdev, ydev, out):
    log("Comparação de estratégias de balanceamento (CV 5 dobras, reamostragem só no treino da dobra)")
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    est = {
        "ponderação de classes": dict(class_weight="balanced", sampler=None),
        "sem balanceamento": dict(class_weight=None, sampler=None),
        "undersampling": dict(class_weight=None, sampler=lambda: RandomUnderSampler(random_state=SEED)),
        "SMOTE": dict(class_weight=None, sampler=lambda: SMOTE(random_state=SEED)),
    }
    linhas = []
    for nome, params in melhores.items():
        for rotulo, cfg in est.items():
            r = []
            for tr, va in skf.split(Xdev, ydev):
                samp = cfg["sampler"]() if cfg["sampler"] else None
                m = make_model(nome, params, sampler=samp, class_weight=cfg["class_weight"])
                m.fit(Xdev.iloc[tr], ydev.iloc[tr])
                p = m.predict_proba(Xdev.iloc[va])[:, 1]
                yv = ydev.iloc[va].values
                c = conf(yv, p, 0.5)
                r.append((c["precisao"], c["recall"], c["f1"], c["fp"], average_precision_score(yv, p)))
            r = np.array(r)
            linhas.append(dict(modelo=nome, estrategia=rotulo,
                               precisao=r[:, 0].mean(), recall=r[:, 1].mean(), f1=r[:, 2].mean(),
                               fp_medio=r[:, 3].mean(), auc_pr=r[:, 4].mean(), auc_pr_dp=r[:, 4].std(ddof=1)))
            log(f"  {nome} / {rotulo}: AUC-PR={r[:,4].mean():.4f} recall={r[:,1].mean():.3f}")
    pd.DataFrame(linhas).to_csv(os.path.join(out, "balanceamento_cv.csv"), index=False)


def main():
    ap = argparse.ArgumentParser()
    pasta_ml = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--csv", default=os.path.join(pasta_ml, "dados", "creditcard.csv"))
    ap.add_argument("--out", default=None,
                    help="pasta de saída (padrão: ml/resultados/sistema ou ml/resultados/ajustada)")
    ap.add_argument("--pular-balanceamento", action="store_true")
    ap.add_argument("--configuracao-sistema", action="store_true",
                    help="usa os hiperparâmetros padrão do ml/train.py em vez da busca em grade")
    a = ap.parse_args()
    if a.out is None:
        a.out = os.path.join(pasta_ml, "resultados",
                             "sistema" if a.configuracao_sistema else "ajustada")
    os.makedirs(a.out, exist_ok=True)

    df = pd.read_csv(a.csv)
    X, y = df.drop(columns="Class"), df["Class"]
    Xdev, Xte, ydev, yte = train_test_split(X, y, test_size=0.30, stratify=y, random_state=SEED)
    info = dict(semente=SEED, n_total=len(df), fraudes_total=int(y.sum()),
                n_dev=len(Xdev), fraudes_dev=int(ydev.sum()),
                n_teste=len(Xte), fraudes_teste=int(yte.sum()),
                cv=f"{N_SPLITS} dobras x {N_REPEATS} repetições", n_arvores_rf=100)
    log(str(info))

    if a.configuracao_sistema:
        # Hiperparâmetros exatos de ml/train.py (padrões do scikit-learn): sem busca em grade
        melhores = {"LR": {"C": 1.0}, "DT": {}, "RF": {}}
        info["configuracao"] = "sistema (ml/train.py, hiperparâmetros padrão)"
    else:
        melhores = tuning(Xdev, ydev, a.out)
        info["configuracao"] = "ajustada por busca em grade"
    info["hiperparametros_escolhidos"] = melhores
    log(f"Escolhidos: {melhores}")
    json.dump(info, open(os.path.join(a.out, "config.json"), "w"), ensure_ascii=False, indent=2)

    _, oof_y, oof_p = cv_repetida(melhores, Xdev, ydev, a.out)
    avaliacao_final(melhores, Xdev, ydev, Xte, yte, oof_y, oof_p, a.out)
    if not a.pular_balanceamento:
        balanceamento(melhores, Xdev, ydev, a.out)
    log("FIM")


if __name__ == "__main__":
    main()

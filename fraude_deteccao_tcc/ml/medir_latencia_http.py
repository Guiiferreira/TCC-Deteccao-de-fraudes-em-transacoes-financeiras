"""
Mede a latência da rota POST /transacoes/classificar com o servidor Flask rodando (RNF01).

Uso: em um terminal suba a API (python app.py); em outro, na raiz do projeto:
    python ml/medir_latencia_http.py

Envia 200 transações do conjunto de teste (mesma divisão do ml/train.py) e mostra média,
mediana, p95 e máximo do tempo de ida e volta e do tempo de inferência medido pelo servidor.
Atenção: cada requisição grava uma transação no banco (fraude_deteccao.db).
"""
import os
import argparse, json, time, urllib.request
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "creditcard.csv")); ap.add_argument("--url", default="http://127.0.0.1:5000")
ap.add_argument("--key", default="tcc-fraude-chave-2026"); ap.add_argument("--n", type=int, default=200)
a = ap.parse_args()
df = pd.read_csv(a.csv)
X, y = df.drop(columns="Class"), df["Class"]
_, Xte, _, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
idx = np.random.default_rng(42).choice(len(Xte), a.n, replace=False)

def post(i):
    row = Xte.iloc[i]
    corpo = json.dumps({"valor": float(row["Amount"]), "features": {k: float(v) for k, v in row.items()}}).encode()
    req = urllib.request.Request(a.url + "/transacoes/classificar", data=corpo, method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": a.key})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as r:
        out = json.loads(r.read())
    return (time.perf_counter() - t0) * 1000, out["tempo_resposta_ms"]

for i in idx[:10]: post(i)  # aquecimento
tot, inf = zip(*[post(i) for i in idx])
for nome, v in (("ida e volta HTTP (cliente)", tot), ("inferência medida pelo servidor", inf)):
    v = np.array(v); print(f"{nome}: média {v.mean():.1f} ms | mediana {np.median(v):.1f} | p95 {np.percentile(v,95):.1f} | máx {v.max():.1f}  (n={len(v)})")

# task1c_20ng_clustering.py (can also be run inside Jupyter)

import os, re
from glob import glob
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# --- Paths ---
BASE = Path.cwd()   # safe for Jupyter
DATA = (BASE / ".." / "Data").resolve()
ROOT = DATA / "20newsgroups"
CSV  = ROOT / "20ng.csv"
FIGS = DATA / "figs"
OUT  = DATA / "task1c_outputs"
FIGS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

# --- Load data ---
def load_20ng():
    if CSV.exists():
        df = pd.read_csv(CSV)
        df = df.dropna(subset=["text"])
        return df[["text","label"]]
    rows = []
    for label_dir in sorted([p for p in ROOT.iterdir() if p.is_dir()]):
        label = label_dir.name
        for f in glob(str(label_dir / "**" / "*"), recursive=True):
            if os.path.isfile(f):
                try:
                    txt = open(f, "r", encoding="utf-8", errors="ignore").read()
                    rows.append((txt, label))
                except Exception:
                    pass
    return pd.DataFrame(rows, columns=["text","label"])

print("[1c] Loading 20NG from:", CSV if CSV.exists() else ROOT)
df = load_20ng()
print("[1c] docs:", len(df), "| labels:", df["label"].nunique())

# --- TF-IDF ---
tfidf = TfidfVectorizer(max_features=120_000, lowercase=True, token_pattern=r"[A-Za-z]+")
X = tfidf.fit_transform(df["text"])

# --- KMeans with silhouette selection ---
k_candidates = [10, 15, 20]
best = None
for k in k_candidates:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    lab = km.fit_predict(X)
    sil = silhouette_score(X, lab, sample_size=min(5000, X.shape[0]), random_state=42)
    print(f"[1c] k={k} | silhouette={sil:.4f}")
    if (best is None) or (sil > best[0]):
        best = (sil, k, km, lab)

best_sil, best_k, best_model, best_labels = best
print(f"[1c] Best k={best_k} (sil={best_sil:.4f})")
pd.Series(best_labels).to_csv(OUT / f"kmeans_labels_k{best_k}.csv", index=False)

# --- PCA visualization ---
subset = min(5000, X.shape[0])
idx = np.random.RandomState(42).choice(X.shape[0], subset, replace=False)
Xp = PCA(n_components=2, random_state=42).fit_transform(X[idx].toarray())

# Plot by cluster
plt.figure(figsize=(9,7))
plt.scatter(Xp[:,0], Xp[:,1], s=6, c=np.array(best_labels)[idx], cmap="tab20", alpha=0.7)
plt.title(f"20NG TF-IDF → KMeans (k={best_k}) — PCA 2D by cluster")
plt.tight_layout()
plt.savefig(FIGS / f"20ng_kmeans_pca_clusters_k{best_k}.png", dpi=180)

# Plot by true label
label_to_int = {l:i for i,l in enumerate(sorted(df["label"].unique()))}
true_colors = df["label"].map(label_to_int).values
plt.figure(figsize=(9,7))
plt.scatter(Xp[:,0], Xp[:,1], s=6, c=true_colors[idx], cmap="tab20", alpha=0.7)
plt.title("20NG TF-IDF — PCA 2D by true label")
plt.tight_layout()
plt.savefig(FIGS / "20ng_pca_true_labels.png", dpi=180)

print("[1c] Saved figures to", FIGS)
print("[1c] Done.")

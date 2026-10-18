# Code cells exported from the saved coursework notebook. Not rerun during portfolio revision.
import numpy, scipy, gensim, sys
from scipy.linalg import triu
print("numpy:", numpy.__version__)
print("scipy:", scipy.__version__)
print("gensim:", gensim.__version__)
print("triu ok:", callable(triu))


# 1b) task1b_news_category_classification.py — TF-IDF + Logistic Regression (and optional W2V)

# Requires: pandas, numpy, scikit-learn, matplotlib, gensim (for W2V part)

# Expects Data/news_category/news.json (Kaggle dataset; fields headline,category).

# task1b_news_category_classification.py  (notebook- & script-friendly)
import re, json, random, sys
from pathlib import Path
import numpy as np
import pandas as pd

# --- sklearn / plotting
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

# --- optional Word2Vec
try:
    from gensim.models import Word2Vec
    USE_W2V = True
except Exception:
    USE_W2V = False

# -------- paths (work in notebook or script) --------
try:
    BASE = Path(__file__).resolve().parent
except NameError:
    BASE = Path.cwd()

DATA = (BASE / ".." / "Data").resolve()
NC_DIR = DATA / "news_category"
FIGS   = DATA / "figs"
OUT    = DATA / "task1b_outputs"
FIGS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

# auto-detect a JSON/JSONL/NDJSON file in news_category
candidates = list(NC_DIR.glob("*.json")) + list(NC_DIR.glob("*.jsonl")) + list(NC_DIR.glob("*.ndjson"))
if not candidates:
    raise FileNotFoundError(f"No JSON file found in {NC_DIR}. Put News_Category_Dataset_v3.json there.")
NEWS = candidates[0]
print("[1b] Using dataset:", NEWS)

# --- load & prep ---
# Kaggle file is JSON-lines (one object per line)
df = pd.read_json(NEWS, lines=True)
# expected fields: headline, category
if "headline" not in df.columns or "category" not in df.columns:
    # Some variants use different field names; try a couple of fallbacks
    text_col = next((c for c in df.columns if c.lower() in {"headline", "title", "text"}), None)
    label_col = next((c for c in df.columns if c.lower() in {"category", "label", "section"}), None)
    if not text_col or not label_col:
        raise ValueError(f"Could not find headline/text and category/label columns in {NEWS}. "
                         f"Columns present: {df.columns.tolist()}")
    df = df.rename(columns={text_col: "text", label_col: "label"})
else:
    df = df.rename(columns={"headline":"text","category":"label"})

df = df[["text","label"]].dropna()
print(f"[1b] Records: {len(df):,} | Labels: {df['label'].nunique()}")

# stratified split
train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
print(f"[1b] train/test: {len(train):,} / {len(test):,}")

# --- Pipeline A: TF-IDF + Logistic Regression ---
tfidf = TfidfVectorizer(max_features=100_000, ngram_range=(1,2),
                        lowercase=True, token_pattern=r"[A-Za-z]+")
X_train = tfidf.fit_transform(train["text"])
X_test  = tfidf.transform(test["text"])

# Use a solver that supports multiclass and can use n_jobs (saga); falls back if unavailable
lr = LogisticRegression(max_iter=300, solver="saga", n_jobs=-1, verbose=0)
lr.fit(X_train, train["label"])
pred = lr.predict(X_test)

print("[1b] TF-IDF + LR report:")
rep = classification_report(test["label"], pred, output_dict=True, zero_division=0)
rep_df = pd.DataFrame(rep).T
rep_df.to_csv(OUT / "tfidf_lr_classification_report.csv")
print(rep_df.head())

# Per-class F1 (top 8 by support)
support = rep_df.iloc[:-3]["support"].sort_values(ascending=False)
top8 = list(support.index[:8])
f1s = rep_df.loc[top8]["f1-score"]

plt.figure(figsize=(10,5))
f1s.plot(kind="bar")
plt.title("Per-class F1 (TF-IDF + LR) — Top 8 frequent labels")
plt.ylabel("F1")
plt.tight_layout()
plt.savefig(FIGS / "news_perclass_f1_tfidf_lr.png", dpi=180)
plt.close()
print("[1b] Saved:", FIGS / "news_perclass_f1_tfidf_lr.png")

# Confusion matrix collapsed to Top-8 + other
label_map = {l:(l if l in top8 else "_other_") for l in test["label"].unique()}
y_true = test["label"].map(label_map)
y_pred = pd.Series(pred, index=test.index).map(label_map)
cm_labels = sorted(set(top8 + ["_other_"]))
cm = confusion_matrix(y_true, y_pred, labels=cm_labels)

plt.figure(figsize=(8,6))
plt.imshow(cm, interpolation="nearest")
plt.xticks(range(len(cm_labels)), cm_labels, rotation=45, ha="right")
plt.yticks(range(len(cm_labels)), cm_labels)
plt.title("Confusion Matrix (Top-8 + other)")
plt.colorbar()
plt.tight_layout()
plt.savefig(FIGS / "news_confusion_matrix_tfidf_lr.png", dpi=180)
plt.close()
print("[1b] Saved:", FIGS / "news_confusion_matrix_tfidf_lr.png")

# --- (Optional) Pipeline B: Avg Word2Vec + LR ---
if USE_W2V:
    print("[1b] Training Word2Vec for average-embeddings baseline...")
    def tokenize(s): return re.findall(r"[A-Za-z]+", str(s).lower())
    train_tokens = [tokenize(t) for t in train["text"]]
    test_tokens  = [tokenize(t) for t in test["text"]]
    w2v = Word2Vec(sentences=train_tokens, vector_size=200, window=5,
                   min_count=5, workers=4, sg=0, epochs=5)

    def avg_vec(tokens):
        vecs = [w2v.wv[w] for w in tokens if w in w2v.wv]
        if not vecs:
            return np.zeros(w2v.vector_size, dtype="float32")
        return np.mean(vecs, axis=0)

    Xtr = np.vstack([avg_vec(toks) for toks in train_tokens])
    Xte = np.vstack([avg_vec(toks) for toks in test_tokens])

    lr2 = LogisticRegression(max_iter=300, solver="saga", n_jobs=-1)
    lr2.fit(Xtr, train["label"])
    p2 = lr2.predict(Xte)
    rep2 = classification_report(test["label"], p2, output_dict=True, zero_division=0)
    pd.DataFrame(rep2).T.to_csv(OUT / "w2v_avg_lr_classification_report.csv")
    print("[1b] W2V-avg + LR macro-F1:", pd.DataFrame(rep2).T.loc["macro avg","f1-score"])

print("[1b] Done. Outputs:")
print(" •", OUT / "tfidf_lr_classification_report.csv")
print(" •", FIGS / "news_perclass_f1_tfidf_lr.png")
print(" •", FIGS / "news_confusion_matrix_tfidf_lr.png")


# ---- (Optional, faster) Pipeline B: Average Word2Vec + LR ----
if USE_W2V:
    print("[1b] Training Word2Vec (fast variant)...")
    def tokenize(s): return re.findall(r"[A-Za-z]+", str(s).lower())
    train_tokens = [tokenize(t) for t in train["text"]]
    test_tokens  = [tokenize(t) for t in test["text"]]

    # ⚡ Lighter settings: smaller vector_size, fewer epochs, higher min_count
    w2v = Word2Vec(
        sentences=train_tokens[:50_000],  # only use ~50k headlines for speed
        vector_size=100,
        window=5,
        min_count=10,   # ignore very rare words
        workers=4,
        sg=0,
        epochs=3
    )

    def avg_vec(tokens):
        vecs = [w2v.wv[w] for w in tokens if w in w2v.wv]
        if not vecs:
            return np.zeros(w2v.vector_size, dtype="float32")
        return np.mean(vecs, axis=0)

    Xtr = np.vstack([avg_vec(toks) for toks in train_tokens])
    Xte = np.vstack([avg_vec(toks) for toks in test_tokens])

    lr2 = LogisticRegression(max_iter=200, n_jobs=4)
    lr2.fit(Xtr, train["label"])
    p2 = lr2.predict(Xte)

    rep2 = classification_report(test["label"], p2, output_dict=True, zero_division=0)
    rep2_df = pd.DataFrame(rep2).T
    rep2_df.to_csv(OUT / "w2v_avg_lr_classification_report_fast.csv")

    print("[1b] W2V-avg + LR macro-F1 (fast):", rep2_df.loc["macro avg","f1-score"])
    print("[1b] Saved:", OUT / "w2v_avg_lr_classification_report_fast.csv")


import re, numpy as np, pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from gensim.models import Word2Vec

BASE = Path.cwd()
DATA = (BASE / ".." / "Data").resolve()
OUT  = DATA / "task1b_outputs"
OUT.mkdir(parents=True, exist_ok=True)

NEWS = next((DATA / "news_category").glob("*.json"))
df = pd.read_json(NEWS, lines=True)[["headline","category"]]\
       .rename(columns={"headline":"text","category":"label"}).dropna()
train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

tokenize = lambda s: re.findall(r"[A-Za-z]+", str(s).lower())
train_tokens = [tokenize(t) for t in train["text"]]
test_tokens  = [tokenize(t) for t in test["text"]]

# FAST settings (smaller model, fewer epochs)
w2v = Word2Vec(sentences=train_tokens, vector_size=100, window=5, min_count=5, workers=4, sg=0, epochs=3)

def avg_vec(tokens):
    vs = [w2v.wv[w] for w in tokens if w in w2v.wv]
    return np.mean(vs, axis=0) if vs else np.zeros(w2v.vector_size, dtype="float32")

Xtr = np.vstack([avg_vec(t) for t in train_tokens])
Xte = np.vstack([avg_vec(t) for t in test_tokens])

from sklearn.linear_model import LogisticRegression
lr = LogisticRegression(max_iter=300, n_jobs=4)
lr.fit(Xtr, train["label"])
p2 = lr.predict(Xte)

rep2 = classification_report(test["label"], p2, output_dict=True, zero_division=0)
pd.DataFrame(rep2).T.to_csv(OUT / "w2v_avg_lr_classification_report_fast.csv")
print("Saved:", OUT / "w2v_avg_lr_classification_report_fast.csv")


from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Resolve dirs (works from your notebooks_or_src notebook too)
BASE = Path.cwd()
DATA = (BASE / ".." / "Data").resolve()
OUT  = DATA / "task1b_outputs"
FIGS = DATA / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

# Known outputs (some may be missing; we’ll skip if not found)
candidates = {
    "TF-IDF + LR": OUT / "tfidf_lr_classification_report.csv",
    "W2V avg + LR": OUT / "w2v_avg_lr_classification_report.csv",
    "W2V avg + LR (fast)": OUT / "w2v_avg_lr_classification_report_fast.csv",
}

scores = {}
for label, path in candidates.items():
    if path.exists():
        df = pd.read_csv(path, index_col=0)
        # row "macro avg", column "f1-score"
        try:
            scores[label] = float(df.loc["macro avg", "f1-score"])
        except Exception:
            pass  # skip if format unexpected

# Make sure we have at least one
assert scores, f"No valid reports found in {OUT}"

# Save summary CSV
summary_csv = OUT / "macro_f1_summary.csv"
pd.Series(scores, name="macro_F1").to_csv(summary_csv, header=True)
print("Saved summary:", summary_csv)

# Plot
labels = list(scores.keys())
vals = [scores[k] for k in labels]

plt.figure(figsize=(8,5))
plt.bar(labels, vals)
plt.title("Macro-F1 Comparison: TF-IDF+LR vs W2V baselines")
plt.ylabel("Macro F1")
plt.ylim(0, 1.0)
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
out_png = FIGS / "news_macroF1_compare.png"
plt.savefig(out_png, dpi=180)
plt.show()

print("Saved figure:", out_png)
for k, v in scores.items():
    print(f"{k}: {v:.3f}")


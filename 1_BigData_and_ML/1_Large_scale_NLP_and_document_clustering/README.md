# 🧠 Machine Learning on Big Data - large-scale NLP and document clustering

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Apache Spark](https://img.shields.io/badge/Spark-3.5-orange)
![NLP](https://img.shields.io/badge/NLP-Text%20Analysis-lightgrey)
![ML](https://img.shields.io/badge/ML-Classification-yellow)

## 📌 Overview
This project explores **large-scale NLP and document clustering** using Apache Spark and Python.  
It applies:

- **Word2Vec embeddings** (semantic representation)
- **TF-IDF + Logistic Regression** (text classification)
- **K-Means clustering** (topic separation)

Datasets include Text8, news headlines, and 20-Newsgroups samples.

---

## 🎯 Objectives
- Train Word2Vec embeddings and test semantic analogies  
- Classify news headlines using TF-IDF vs Word2Vec  
- Cluster documents and visualize with PCA projections  

---

## 🛠️ Technology Stack
`Python` · `Apache Spark` · `MLlib` · `scikit-learn` · `NLTK` · `Matplotlib`  

---

## 🔬 Workflow Summary
### **Task 1a — Word2Vec Embeddings**
- Trained embeddings on Text8  
- Nearest-neighbor queries:  
  - *king → queen*, *Britain → England*, etc.  
- Demonstrated strong semantic cohesion  

### **Task 1b — Text Classification**
Models tested:

| Model | Features | Macro-F1 |
|------|----------|----------|
| Logistic Regression | TF-IDF | **0.42** |
| Logistic Regression | Word2Vec avg vectors | 0.23 |

TF-IDF significantly outperformed Word2Vec for headline classification.

### **Task 1c — Document Clustering**
- K-Means (k = 20) applied on sparse vectors  
- Silhouette score ≈ **–0.008** → expected weak separation  
- PCA used to visualize topic overlap  

---

## 📊 Deliverables
- Word2Vec semantic similarity results  
- Confusion matrix + classification metrics  
- PCA and K-Means visualizations  

---

## 🚀 Next Steps
- Replace TF-IDF with **BERT embeddings**  
- Use **UMAP** for better dimensionality reduction  
- Experiment with **Spectral** and **Agglomerative** clustering  


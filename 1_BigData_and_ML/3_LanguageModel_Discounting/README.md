# 🔤 Frequency Estimation & Discounting for Language Models

![PySpark](https://img.shields.io/badge/PySpark-Analytics-orange)
![NLP](https://img.shields.io/badge/NLP-Language%20Modeling-blue)
![Stats](https://img.shields.io/badge/Statistics-Smoothing-green)

## Overview
This project implements **N-gram probability estimators** using PySpark:

- **Maximum Likelihood Estimation (MLE)**
- **Good–Turing Smoothing**
- **Absolute Discounting (AD)**

Evaluation focuses on **rare-event probability correction**, divergence metrics, and Zipfian behavior.

---

## Objectives
- Compare estimator performance at multiple sample sizes  
- Quantify divergence from reference “full corpus” distribution  
- Visualize rank-frequency and tail behavior  

---

## Stack
`PySpark` · `NumPy` · `pandas` · `matplotlib`  

---

## Key Findings

### **Good–Turing**
- Best for long-tail corrections  
- Stabilizes rare-event probability mass  

### **Absolute Discounting**
- Most stable across mid-frequency tokens  

### **MLE**
- Overfits high-frequency words  
- Fails on sparse vocabularies  

### Convergence
All estimators begin stabilizing by **~1 million tokens**.

---

## Deliverables
- Zipf curves  
- Divergence plots (KL, JS, L1)  
- Smoothing comparison tables  

---

## Next Steps
- Extend to **Kneser–Ney smoothing**  
- Implement a small **backoff language model**  
- Integrate into a streaming text pipeline  


# 📊 Hadoop MapReduce Data Processing Lab  
**Big Data • Distributed Computing • HDFS • Batch Analytics**

![Hadoop](https://img.shields.io/badge/Hadoop-MapReduce-yellow)
![BigData](https://img.shields.io/badge/Big%20Data-Distributed%20Processing-blue)
![Linux](https://img.shields.io/badge/Linux-HDFS-success)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

---

## 🚀 Project Overview

This lab demonstrates hands-on experience with **Apache Hadoop MapReduce** for processing large datasets in a **distributed computing environment**.

The focus is on:

- Storing data in **HDFS**  
- Running **MapReduce jobs**  
- Performing batch data processing  
- Understanding distributed execution  
- Analyzing output results  

This mirrors how big data pipelines operate in **cloud and enterprise data platforms**.

---

## 🎯 Objectives

- Upload datasets to HDFS  
- Run MapReduce jobs  
- Process data in parallel  
- Generate analytical outputs  
- Understand Hadoop architecture  
- Practice Linux-based data engineering  

---

## 🛠️ Tools & Environment

| Component | Purpose |
|----------|---------|
| Apache Hadoop | Distributed processing |
| HDFS | Distributed file storage |
| MapReduce | Batch computation |
| Linux (VM) | Execution environment |
| Java | Job execution |
| Cloudera / Standalone Hadoop | Platform |

---

## 🏗️ Hadoop Architecture Overview

```text
Input Data
   |
   v
HDFS (Distributed Storage)
   |
   v
Map Phase (Parallel Processing)
   |
   v
Shuffle & Sort
   |
   v
Reduce Phase (Aggregation)
   |
   v
Output Results (HDFS)
```

---

## 🧪 Lab Implementation

### 1️⃣ Data Ingestion (HDFS)

- Uploaded datasets to HDFS  
- Verified file replication  
- Confirmed directory structure  

```bash
hdfs dfs -mkdir /input
hdfs dfs -put data.txt /input
```

---

### 2️⃣ MapReduce Job Execution

- Ran built-in Hadoop MapReduce jobs  
- Processed large text datasets  
- Observed distributed execution  

```bash
hadoop jar hadoop-mapreduce-examples.jar wordcount /input /output
```

---

### 3️⃣ Output Analysis

- Retrieved results from HDFS
- Verified word counts
- Interpreted output
- hdfs dfs -cat /output/part-r-00000

---

## 📊 Results

- ✅ Data processed successfully
- ✅ Distributed execution confirmed
- ✅ Output generated in HDFS
- ✅ Batch analytics completed
- ✅ Pipeline reproducible

---

## 🔍 Key Learnings

- Hadoop enables scalable batch processing
- HDFS supports fault-tolerant storage
- MapReduce splits work across nodes
- Shuffle & Sort are critical stages
- Linux CLI is essential for data engineering

---

## 🧠 Data Engineering Skills Demonstrated

- HDFS file management
- MapReduce job execution
- Distributed processing
- Batch analytics
- Linux command-line usage
- Data pipeline validation

---

## 🔐 Security & Governance Context

| Principle | Relevance |
|----------|-----------|
| Access Control | HDFS permissions |
| Data Integrity | Replication & checks |
| Fault Tolerance | Node failure handling |
| Auditability | Job logs |
| Data Governance | Structured outputs |

---

## 📁 Repository Structure

```text
hadoop-mapreduce-lab/
├── README.md
├── input/
│   └── data.txt
├── output/
│   └── part-r-00000
├── screenshots/
│   ├── hdfs-upload.png
│   ├── job-run.png
│   └── output-results.png
└── docs/
    └── lab-report.pdf
```

---

### 💼 Resume Bullet

**Executed Hadoop MapReduce jobs on HDFS** to process large datasets using distributed batch processing, demonstrating data engineering, Linux administration, and scalable analytics skills.

---

## 🚫 Scope & Limitations

- Single-node / lab cluster  
- Batch processing only  
- No real-time streaming  
- No cloud-managed Hadoop  

---

## 🔮 Future Enhancements

- Spark integration  
- Hive queries  
- Cloud-based Hadoop (EMR / Dataproc)  
- Real-time pipelines  
- Secure Kerberos setup  

---

## 🎯 Why This Lab Matters

This project demonstrates:

- Big data processing skills  
- Distributed systems understanding  
- Data engineering fundamentals  
- Infrastructure awareness  
- Analytical problem-solving  

It aligns with roles such as:

- Data Engineer  
- Cloud Engineer  
- Big Data Analyst  
- Analytics Engineer  
- Platform Engineer  

---

## 👤 Author

**Godwin Etim Akpan**  
GIS | Big Data | Cybersecurity | Cloud Computing

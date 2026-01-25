# 🌐 Streaming Analytics with PySpark — NASA HTTP Logs

![Spark](https://img.shields.io/badge/Spark-Structured%20Streaming-orange)
![BigData](https://img.shields.io/badge/Data-RealTime-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)

## Overview
This project simulates **real-time ingestion and analysis of NASA server logs** using Spark Structured Streaming.

It demonstrates:

- Windowed aggregations  
- Throughput & latency monitoring  
- Detection of anomaly spikes (404/500)  

---

## Objectives
- Build a streaming job that consumes log lines  
- Monitor HTTP status code trends  
- Evaluate performance: input rates, batch durations, memory usage  

---

## Stack
`Spark Structured Streaming` · `Python` · `HDFS` · `PowerShell feeder`  

---

## Workflow

### **1. Log Feeder**
A PowerShell script streams NASA logs line-by-line to a socket.

### **2. Spark Streaming Job**
- Reads socket input  
- Aggregates events in **1-minute tumbling windows**  
- Applies watermarking for late data  

### **3. Monitoring**
- Batch duration 1.8–2.5 seconds  
- Input rate > **10,000 rows/sec**  
- Detectable spikes in 404 & 500 series errors  

---

## Deliverables
- Throughput vs time plot  
- Latency/batch duration plot  
- Streaming dashboard screenshots  

---

## Next Steps
- Replace socket with **Kafka topic**  
- Persist results to **Elasticsearch**  
- Train streaming anomaly detection model  


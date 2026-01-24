# ☁️ CloudSim Scheduling Algorithms – Cloud Performance Simulation Project  
**Custom Scheduling • Performance Analysis • Cloud Systems Modeling**

![Status](https://img.shields.io/badge/Status-Completed-brightgreen)
![CloudSim](https://img.shields.io/badge/CloudSim-Simulation-blue)
![Java](https://img.shields.io/badge/Java-Modeling-orange)
![Cloud](https://img.shields.io/badge/Cloud-Systems%20Modeling-success)

---

## Project Overview

This project examines **task scheduling behaviour in cloud computing environments** using **CloudSim**, a widely adopted cloud simulation framework used in research and industry-facing performance studies.

The work focuses on **implementing and evaluating custom cloudlet scheduling algorithms** to understand how scheduling decisions influence **execution order, waiting time, and turnaround time** under controlled conditions.

The project builds on academic cloud computing foundations and extends them through **independent implementation, analysis, and interpretation**, with an emphasis on clarity, reproducibility, and practical insight rather than coursework-style demonstration.

---

## Project Focus

- Model cloud execution workflows using simulation  
- Implement and evaluate **custom cloudlet scheduling algorithms**  
- Compare execution behaviour under **identical workloads**  
- Analyse scheduling outcomes using **reproducible metrics**  
- Translate scheduling theory into **practical systems insight**  

---

## Context & Motivation

Scheduling decisions play a critical role in cloud and distributed systems, directly influencing:

- **Throughput**  
- **Latency**  
- **Fairness**  
- **Resource utilisation**  

While commercial cloud platforms rely on complex and proprietary schedulers, **foundational algorithms** such as:

- First-Come, First-Served (FCFS)  
- Shortest Job First (SJF)  
- Priority Scheduling  

remain essential for understanding how scheduling policies behave under different workload conditions.

This project uses **CloudSim** to isolate scheduler behaviour in a **transparent and repeatable environment**, allowing clear observation of cause-and-effect relationships without infrastructure noise.

---

## Tools & Environment

- **CloudSim** – Discrete-event cloud simulation toolkit  
- **Java** – Scheduler and simulation logic  
- **Eclipse IDE** – Development environment  
- **CSV outputs** – Structured performance metrics  
- **Python** – Post-simulation analysis  

---

## Conceptual Architecture

```text
User / Broker
     |
 Cloudlets (Tasks)
     |
 Virtual Machine
     |
 Cloudlet Scheduler
     |
 Host
     |
 Datacenter
     |
 CloudSim Engine
```

This simplified execution pipeline reflects core cloud scheduling concepts while keeping the analysis focused on scheduler behaviour rather than infrastructure complexity.

---

## Scheduling Algorithms Implemented

This project implements **custom `CloudletScheduler` classes** that are **not provided by default in CloudSim**, enabling controlled evaluation of foundational scheduling strategies.

### First-Come, First-Served (FCFS)

- Executes tasks strictly in order of arrival
- Serves as a deterministic baseline for comparison

### Shortest Job First (SJF)

- Prioritises tasks with shorter execution lengths
- Reduces average waiting time under **heterogeneous workloads**

### Priority Scheduling

- Executes tasks based on assigned priority values
- Reflects service differentiation strategies used in practice

Each scheduler was evaluated using **identical workloads** to ensure a fair and controlled comparison.

---

## Simulation Design

The simulation environment was intentionally kept simple to isolate scheduler behaviour.

- Single datacenter and single host
- One virtual machine
- Space-shared execution model
- Ten homogeneous cloudlets
- Equal computational length per cloudlet

This design removes confounding variables, allowing differences in **scheduler behaviour**, rather than resource variation, to be observed.

---

## Results Summary

| Scheduler | Avg Waiting Time | Avg Turnaround Time | Avg Finish Time |
|----------|------------------:|--------------------:|----------------:|
| FCFS     | 1800.0            | 400.0               | 4000.1          |
| SJF      | 1800.0            | 400.0               | 4000.1          |
| Priority | 1800.0            | 400.0               | 4000.1          |

---

## Key Insights

- When workloads are **homogeneous**, scheduling algorithms converge in performance
- **SJF behaves like FCFS** when task lengths are identical
- **Priority scheduling changes execution order**, not total execution time
- Performance differences emerge primarily under **heterogeneous workloads**

These observations reinforce established scheduling theory and provide intuition applicable to real cloud and batch-processing systems.

---

## Repository Structure

```text
cloudsim-scheduling-project/
├── README.md
├── src/
│   ├── FCFSCloudletScheduler.java
│   ├── SJFCloudletScheduler.java
│   ├── PriorityCloudletScheduler.java
│   └── SchedulerComparison.java
├── results/
│   ├── fcfs.csv
│   ├── sjf.csv
│   └── priority.csv
├── screenshots/
│   └── eclipse-execution.png
└── docs/
    └── analysis-report.pdf
```

---

## Practical Relevance

Although CloudSim is a simulation tool, the concepts demonstrated here translate directly to:

- Cloud workload scheduling
- Batch and queue-based processing systems
- Distributed computing platforms
- Container orchestration principles
- Performance benchmarking workflows

The project builds foundational understanding relevant to **AWS, Azure, GCP, Kubernetes, and HPC environments**.

---

## Scope and Constraints

- Simulation-based (no real cloud deployment)
- Single VM and host
- No network latency modelling
- No energy or cost optimisation

These constraints were intentional to preserve analytical clarity.

---

## Future Directions

- Heterogeneous task workloads
- Multi-VM and multi-host scenarios
- Time-shared execution models
- Energy-aware scheduling
- Adaptive or ML-based schedulers

---

## Author

**Godwin Etim Akpan**  
Big Data • Cloud Computing • GIS • Cybersecurity

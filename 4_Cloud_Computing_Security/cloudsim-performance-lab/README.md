# ☁️ CloudSim Performance Simulation Lab  
**Cloud Modeling • Resource Allocation • Performance Evaluation**

![CloudSim](https://img.shields.io/badge/CloudSim-Simulation-blue)
![Java](https://img.shields.io/badge/Java-Modeling-orange)
![Cloud](https://img.shields.io/badge/Cloud-Performance%20Analysis-success)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

---

## 🚀 Project Overview

This lab demonstrates the use of **CloudSim**, a cloud computing simulation framework, to model and evaluate:

- Virtual machine (VM) allocation  
- Cloudlet (task) scheduling  
- Data center performance  
- Resource utilization  
- Cloud infrastructure efficiency  

Instead of deploying real cloud resources, **CloudSim allows controlled experimentation** to analyze how cloud systems behave under different workloads and configurations.

This is widely used in **cloud research, performance engineering, and academic studies**.

---

## 🎯 Objectives

- Simulate cloud data center environments  
- Configure hosts, VMs, and cloudlets  
- Evaluate task execution performance  
- Compare scheduling and allocation policies  
- Analyze response time and resource usage  
- Understand cloud scalability behavior  

---

## 🛠️ Tools & Environment

| Component | Purpose |
|----------|---------|
| CloudSim | Cloud simulation framework |
| Java | Simulation programming |
| Eclipse / IntelliJ | Development IDE |
| JVM | Execution environment |
| CSV / Logs | Output analysis |

---

## 🏗️ Simulation Architecture

```text
User Workload
   |
Cloudlets (Tasks)
   |
VMs (Virtual Machines)
   |
Hosts (Physical Servers)
   |
Datacenter
   |
CloudSim Simulation Engine
```

---

## 🧪 Lab Implementation

### 1️⃣ Datacenter Configuration

- Defined physical hosts (CPU, RAM, storage, bandwidth)  
- Configured processing elements (PEs)  
- Established resource capacities  

📸 *Screenshot: Datacenter Configuration Code*

---

### 2️⃣ Virtual Machine (VM) Setup

Created VMs with:

- CPU cores  
- RAM  
- Bandwidth  

Assigned scheduling policies.

📸 *Screenshot: VM Configuration*

---

### 3️⃣ Cloudlet (Task) Creation

- Defined computational workloads  
- Assigned instruction lengths  
- Mapped tasks to VMs  

📸 *Screenshot: Cloudlet Setup*

---

### 4️⃣ Scheduling Policies

Tested:

- Time-shared scheduling  
- Space-shared scheduling  

Compared execution efficiency.

📸 *Screenshot: Scheduling Configuration*

---

### 5️⃣ Simulation Execution

- Started CloudSim engine  
- Monitored execution logs  
- Captured performance metrics  

📸 *Screenshot: Simulation Output*

---

## 📊 Results

- ✅ Tasks executed successfully  
- ✅ VM utilization measured  
- ✅ Scheduling behavior observed  
- ✅ Performance metrics collected  
- ✅ Simulation reproducible  

---

## 🔍 Key Learnings

- CloudSim enables cost-free performance testing  
- Scheduling policies impact execution time  
- VM sizing affects throughput  
- Cloud modeling helps predict real-world behavior  
- Simulation supports research and optimization  

---

## 🧠 Cloud Engineering Skills Demonstrated

- Cloud architecture modeling  
- Resource allocation analysis  
- Performance benchmarking  
- Scheduling policy evaluation  
- Infrastructure simulation  
- Data interpretation  

---

## 🔐 Security & Governance Context

While CloudSim is a simulation tool, this lab supports:

| Principle | Relevance |
|----------|-----------|
| Capacity Planning | Prevents over-provisioning |
| Resilience Testing | Identifies bottlenecks |
| Risk Reduction | Avoids misconfiguration |
| Cost Optimization | Predicts resource needs |

---

## 📁 Repository Structure

```text
cloudsim-performance-lab/
├── README.md
├── src/
│   └── CloudSimSimulation.java
├── results/
│   ├── output.log
│   └── metrics.csv
├── screenshots/
│   ├── datacenter.png
│   ├── vm-config.png
│   ├── cloudlets.png
│   └── results.png
└── docs/
    └── analysis-report.pdf
```

---

## 💼 Resume Bullet

**Simulated cloud infrastructure performance using CloudSim (Java)** by modeling data centers, virtual machines, and workloads to evaluate scheduling policies, resource utilization, and execution efficiency.

---

## 🚫 Scope & Limitations

- Simulation environment (not real cloud)  
- No real network latency  
- No security attack modeling  
- Academic workload models  

---

## 🔮 Future Enhancements

- Energy consumption modeling  
- Multi-datacenter simulation  
- SLA violation analysis  
- Fault tolerance scenarios  
- Hybrid cloud simulation  

---

## 🎯 Why This Lab Matters

This project demonstrates:

- Cloud engineering research skills  
- Performance optimization understanding  
- Infrastructure modeling capability  
- Analytical thinking  
- System design evaluation  

It aligns with roles such as:

- Cloud Engineer  
- Performance Engineer  
- Cloud Architect  
- Research Engineer  
- Infrastructure Analyst  

---

## 👤 Author

**Godwin Etim Akpan**  
GIS | Big Data | Cybersecurity | Cloud Computing  

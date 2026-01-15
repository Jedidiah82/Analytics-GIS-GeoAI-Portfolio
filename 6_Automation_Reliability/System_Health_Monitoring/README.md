# 📌 Project Title  
## System Health Monitoring & Automated Alerting  

---

## 🧠 Overview  

This project implements an automated **system health monitoring tool** that continuously checks critical infrastructure metrics and sends **email alerts** when thresholds are exceeded.  

It simulates real-world **IT operations, DevOps, and reliability engineering** workflows used in enterprise environments to ensure system availability and prevent downtime.  

---

## 🎯 Objectives  

The system monitors:  

- **CPU usage** (> 80%)  
- **Disk space** (< 20%)  
- **Available memory** (< 100MB)  
- **Hostname resolution** (localhost → 127.0.0.1)  

If any condition fails, an automated **alert email** is sent to administrators.  

---

## 🛠️ Tools & Technologies  

| Category | Tools |
|---------|-------|
| Language | Python |
| Monitoring | psutil, shutil |
| Networking | socket |
| Automation | cron |
| Alerts | SMTP |
| OS | Linux |

---

## ⚙️ How It Works  

- Collects system metrics using `psutil`  
- Evaluates against predefined thresholds  
- Detects DNS resolution failures  
- Sends alert email if an issue is found  
- Can be scheduled with `cron` to run every 60 seconds  

---

## 🧪 Key Features  

- 🔍 Real-time system diagnostics  
- 📧 Automated email alerts  
- 🕒 Scheduled monitoring via cron  
- 🛡️ Reliability-focused checks  
- 📈 Infrastructure readiness validation  

---

## 🗂️ Project Structure  

```text
system_health_monitoring/
│
├── health_check.py
├── emails.py
└── README.md
```

---

## 🚀 Example Use Case  

This tool can be used in:  

- IT Support Operations  
- DevOps Monitoring  
- Cloud Infrastructure Health Checks  
- Cybersecurity SOC environments  
- Data Engineering reliability workflows  

---

## 📌 Sample Alert Scenarios  

| Condition | Alert Triggered |
|----------|------------------|
| CPU > 80% | Yes |
| Disk < 20% | Yes |
| Memory < 100MB | Yes |
| DNS Failure | Yes |

---

## 📎 Skills Demonstrated  

- System monitoring  
- Python automation  
- Infrastructure reliability  
- Alerting systems  
- Linux task scheduling  
- Operational resilience  

---

## 🔗 Related Portfolio Pillar  

Part of:  
**⚙️🛡️📊 Automation, Reliability & Secure Data Systems**  

---

## 🧭 Next Steps  

Planned improvements:  

- Slack / Teams alert integration  
- Grafana dashboard  
- Dockerized deployment  
- Cloud monitoring (AWS / Azure)  

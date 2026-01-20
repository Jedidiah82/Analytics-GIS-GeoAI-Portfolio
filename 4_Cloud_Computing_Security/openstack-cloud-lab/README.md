# ☁️ OpenStack Cloud Network & VM Deployment Lab  
**Private Cloud Infrastructure • Virtual Networking • Secure VM Provisioning**

---

## 🚀 Project Overview

This lab demonstrates hands-on experience deploying and managing **virtual machines (VMs)** and **cloud networking** in a **private OpenStack environment**.

The focus is on:

- Cloud infrastructure provisioning  
- Virtual networking (subnets, routers, security groups)  
- Secure VM access using SSH keys  
- Tenant-based isolation  
- Cloud architecture fundamentals  

This mirrors how **enterprise and research private clouds** are built outside of AWS and Azure.

---

## 🎯 Objectives

- Create a private cloud network  
- Configure subnets and routing  
- Deploy virtual machines  
- Implement security groups (firewall rules)  
- Enable secure SSH access  
- Understand tenant-based cloud isolation  
- Apply cloud architecture concepts in a private cloud  

---

## 🛠️ Tools & Environment

| Component | Purpose |
|----------|---------|
| OpenStack Horizon | Web-based management dashboard |
| Nova | Compute (VM provisioning) |
| Neutron | Networking |
| Glance | Image management |
| Linux Images | Ubuntu / CirrOS |
| SSH Key Pairs | Secure VM access |

**Environment:** University / Lab-hosted OpenStack private cloud

---

## 🏗️ Architecture Overview

```text
User
  |
  | Horizon Dashboard / OpenStack CLI
  |
OpenStack Control Plane
  |
  +-- Neutron (Networking)
  |      ├─ Private Subnet
  |      ├─ Router
  |      └─ Security Groups
  |
  +-- Nova (Compute)
  |      └─ Virtual Machine (Ubuntu)
  |
  +-- Glance (Images)
```

---

## 🔐 Security Design

| Control | Implementation |
|--------|----------------|
| Network Isolation | Tenant-based private networks |
| Firewall Rules | Security groups (port-level access) |
| Authentication | OpenStack user credentials |
| VM Access | SSH key-based authentication |
| Least Privilege | Restricted inbound access |

---

## 🧪 Lab Implementation

### 1️⃣ Network Creation

- Created a **private tenant network**  
- Assigned a **subnet** with internal IP range  
- Enabled **DHCP** for VM addressing  

📸 *Screenshot: Network & Subnet Configuration*

---

### 2️⃣ Router Setup

- Connected private subnet to **external network**  
- Enabled **outbound internet access**  

📸 *Screenshot: Router Topology*

---

### 3️⃣ Security Groups

Configured firewall rules:

| Port | Purpose |
|------|--------|
| 22 | SSH |
| 80 | HTTP (optional) |
| ICMP | Ping |

📸 *Screenshot: Security Group Rules*

---

### 4️⃣ Key Pair Generation

- Created **SSH key pair** for secure VM access  
- Avoided password-based authentication  

📸 *Screenshot: Key Pair Management*

---

### 5️⃣ VM Deployment

- Selected **Ubuntu image**  
- Assigned **compute flavor** (CPU/RAM)  
- Attached **network**  
- Applied **security group**  
- Injected **SSH key**  

📸 *Screenshot: Instance Creation*

---

### 6️⃣ Secure Access

```bash
ssh -i openstack-key.pem ubuntu@<floating-ip>
```

---

### ✅ Verification

The following were successfully verified:

- User access  
- Network connectivity  
- System information  

📸 *Screenshot: SSH Session*

---

## 📊 Results

- ✅ VM successfully deployed  
- ✅ Secure SSH access achieved  
- ✅ Network routing functional  
- ✅ Firewall rules enforced  
- ✅ Private cloud isolation confirmed  

---

## 🔍 Key Learnings

- OpenStack mirrors enterprise private cloud design  
- Networking configuration is more explicit than AWS/Azure  
- Security groups act as cloud firewalls  
- Tenant isolation is critical in shared clouds  
- SSH keys remain the industry standard for secure access  

---

## 🧠 Cloud Architecture Skills Demonstrated

- Virtual networking  
- Compute provisioning  
- Security segmentation  
- Identity-based access  
- Cloud resource orchestration  
- Infrastructure troubleshooting  

---

## 🔐 Security Framework Alignment (NIST CSF)

| Function | Applied |
|---------|--------|
| Identify | Cloud resources, networks, VMs |
| Protect | Security groups, SSH keys |
| Detect | Access validation |
| Respond | Rule adjustments |
| Recover | VM redeployment |

---

## 📁 Repository Structure

```text
openstack-cloud-lab/
├── README.md
├── network-diagrams/
│   └── openstack-topology.png
├── screenshots/
│   ├── network.png
│   ├── router.png
│   ├── security-group.png
│   ├── instance.png
│   └── ssh-access.png
└── configs/
    └── security-group-rules.txt
```

---

## 💼 Resume Bullet

**Deployed and secured virtual machines in a private OpenStack cloud environment** by configuring tenant networks, subnets, routers, security groups, and SSH-based access, demonstrating cloud infrastructure and network security fundamentals.

---

## 🚫 Scope & Limitations

- Lab environment (not production)  
- No high availability  
- Manual provisioning  
- No automation (yet)  

---

## 🔮 Future Enhancements

- OpenStack CLI automation  
- Terraform integration  
- Multi-VM deployments  
- Load balancer configuration  
- Network segmentation policies  

---

## 🎯 Why This Lab Matters

This project demonstrates:

- Multi-cloud infrastructure understanding  
- Real networking skills  
- Security-first cloud design  
- Enterprise cloud architecture knowledge  

It aligns with roles such as:

- Cloud Engineer  
- Infrastructure Engineer  
- Security Engineer  
- DevOps Engineer  

---

## 👤 Author

**Godwin Etim Akpan**  
GIS | Big Data | Cybersecurity | Cloud Computing
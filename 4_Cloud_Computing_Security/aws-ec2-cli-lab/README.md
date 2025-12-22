# 🚀 AWS EC2 Provisioning & Monitoring via AWS CLI (PowerShell)
> **Hands-on AWS project demonstrating EC2 provisioning, IAM security, monitoring, and cost control using AWS CLI on Windows PowerShell.**

![AWS](https://img.shields.io/badge/AWS-CLI-orange)
![PowerShell](https://img.shields.io/badge/PowerShell-Windows-blue)
![EC2](https://img.shields.io/badge/EC2-t3.micro-success)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

---

## 📌 Project Summary

This project demonstrates **end-to-end AWS infrastructure provisioning using AWS CLI v2 on Windows PowerShell**, without relying on the AWS Management Console.

The lab covers:

- IAM authentication & access keys  
- EC2 provisioning via CLI  
- Secure SSH access  
- CloudWatch monitoring  
- IAM least-privilege experimentation  
- Real-world permission troubleshooting  
- Cost-safe cleanup  
- Full infrastructure lifecycle automation mindset and cost awareness  

> **All resources were created, verified, and destroyed using AWS CLI commands.**

---

## ✅ Prerequisites

- AWS account (Free Tier)
- IAM user with programmatic access
- AWS CLI v2 installed
- Windows PowerShell
- Basic understanding of Linux & SSH

---

## 🎯 Objectives

- Provision EC2 using AWS CLI  
- Authenticate securely with IAM  
- Understand region-specific AMIs  
- Enable monitoring  
- Practice least-privilege IAM  
- Document infrastructure professionally  
- Prepare portfolio-ready artifacts  

---

## 🧠 Skills Demonstrated

- AWS CLI v2 (Windows / PowerShell)  
- IAM Users, Policies & MFA  
- EC2 lifecycle management  
- SSH with key pairs  
- CloudWatch metrics  
- IAM permission troubleshooting  
- Cost-aware AWS usage  
- Infrastructure documentation  
- Security-first cloud practices  

---

## 🏗️ Architecture Overview

### High-Level Architecture

```text
+----------------------+
| Local Workstation    |
| Windows 11           |
| PowerShell + AWS CLI |
+----------+-----------+
           |
           | AWS API Calls
           v
+----------------------+
| AWS IAM              |
| - IAM User           |
| - Access Keys        |
| - Policies           |
+----------+-----------+
           |
           | Authorized Requests
           v
+----------------------+
| Amazon EC2           |
| - Amazon Linux 2023  |
| - t3.micro           |
+----------+-----------+
           |
           | Metrics
           v
+----------------------+
| Amazon CloudWatch    |
| - CPU Utilization    |
| - Status Checks     |
+----------------------+
```

📸 **Screenshot Placeholder 1 – Architecture Diagram**
![Architecture Diagram](diagrams/aws-ec2-cli-architecture.png)

## 📁 Repository Structure

```
aws-ec2-cli-lab/
├── README.md
├── diagrams/
│   ├── aws-ec2-cli-architecture.png
│   └── iam-auth-flow.png
├── policies/
│   └── ec2-cli-least-privilege.json
├── scripts/
│   ├── create-ec2.ps1
│   ├── terminate-ec2.ps1
│   └── monitoring.ps1
```

## 🔐 IAM Setup
> IAM policies were attached incrementally to observe permission boundaries and AccessDenied behavior.

### IAM User
- **User name:** ec2-admin
- **Authentication:** Access Key + Secret Key
- **MFA:** Enabled for root user

### Policies Used
- AdministratorAccess (for labs & learning)
- IAMUserChangePassword
- Custom least-privilege policy (tested)


📸 **Screenshot Placeholder 2 – IAM Policies**
![IAM Policies](diagrams/iam-user-policies.png)

## 🖥️ Local Environment
### Tools
- Windows 11
- PowerShell
- AWS CLI v2

Verify AWS CLI:
```powershell
aws --version
```

📸 **Screenshot Placeholder 3 – AWS CLI Version**
![AWS CLI Version](diagrams/aws-cli-version.png)


## 🔑 AWS CLI Configuration
```powershell
aws configure
```
Provided values:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: us-east-2
- Output format: json

Verification:
```powershell
aws sts get-caller-identity
```

📸 **Screenshot Placeholder 4 – STS Identity**
![STS Identity](diagrams/aws-sts-identity.png)


## 🔐 EC2 Key Pair Creation (CLI)
```powershell
aws ec2 create-key-pair `
  --key-name week10-cli-key `
  --query "KeyMaterial" `
  --output text > week10-cli-key.pem
```

📸 **Screenshot Placeholder 5 – Key Pair CLI**
![Key Pair CLI](diagrams/ec2-keypair-cli.png)


## 🧩 AMI Discovery (Region-Aware)
> All resources were deployed in **us-east-2 (Ohio)**.

AMIs are region-specific. Latest Amazon Linux 2023 AMI was queried dynamically:
```powershell
aws ec2 describe-images `
  --owners amazon `
  --filters "Name=name,Values=al2023-ami-*-x86_64" `
  --query "Images | sort_by(@, &CreationDate)[-1].ImageId" `
  --output text
```

Result:

```bash
ami-06ba285c80bc4ab50
```

## 🚀 EC2 Instance Creation (CLI)
> The default EC2 security group was used for this lab, allowing SSH (port 22) access from the local workstation.

```powershell
aws ec2 run-instances `
  --image-id ami-06ba285c80bc4ab50 `
  --instance-type t3.micro `
  --key-name week10-cli-key `
  --security-groups launch-wizard-1 `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Week10-EC2-CLI}]"
```

📸 **Screenshot Placeholder 6 – EC2 Instance Running (Console View)**
![EC2 Running](diagrams/ec2-instance-running.png)


## 🔑 SSH Access
```bash
ssh -i week10-cli-key.pem ec2-user@<PUBLIC-IP>
```

Verification on the instance:
```bash
whoami
uname -a
```

📸 **Screenshot Placeholder 7 – SSH Session**
![SSH Session](diagrams/ssh-session.png)


## 📊 CloudWatch Monitoring
Enabled metrics:
- CPUUtilization
- Status checks
- Ready for alarms & dashboards


📸 **Screenshot Placeholder 8 – CloudWatch Metrics**
![CloudWatch Metrics](diagrams/cloudwatch-metrics.png)


## 🔐 Least-Privilege IAM Experiment
Custom policy tested:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

**Outcome**
- Expected AccessDenied errors observed
- IAM enforcement validated
- AdministratorAccess restored for continued practice

📸 **Screenshot Placeholder 9 – Access Denied**
![Access Denied](diagrams/access-denied-errors.png)


## 🧹 Resource Cleanup

```powershell
aws ec2 terminate-instances `
  --instance-ids i-04f7de3181b806f12
```
✔ Instance terminated
✔ No ongoing charges

📸 **Screenshot Placeholder 10 – EC2 Terminated**
![EC2 Terminated](diagrams/ec2-terminated.png)


## 🧠 Key Decisions & Lessons Learned

- **AWS CLI over Console:** Used the AWS CLI instead of the Management Console to enable automation, repeatability, and production-like workflows.
- **Region-specific AMIs:** Learned that AMI IDs are region-specific and must be queried dynamically to avoid deployment failures.
- **Least-Privilege Enforcement:** Observed how least-privilege IAM policies intentionally block unauthorized and administrative actions.
- **IAM Permission Boundaries:** Understood why IAM users cannot self-escalate permissions and how AWS prevents privilege escalation.
- **Cost Control Practices:** Practiced safe cost management by explicitly terminating EC2 resources after use.


## 🤔 Why AWS CLI Instead of Console?

- Enables automation and scripting
- Ensures repeatability across environments
- Mirrors production DevOps workflows
- Reduces configuration drift


## 🔐 Security Considerations

- Root account protected with MFA
- IAM user used instead of root for daily operations
- Temporary use of AdministratorAccess for labs
- Least-privilege policy tested and documented
- SSH access restricted via key pair authentication


## 📏 Scope & Limitations

- Single EC2 instance (no Auto Scaling)
- No production networking (VPC defaults used)
- AdministratorAccess used temporarily for learning
- Not intended for production workloads


## 🚫 What This Project Is Not

- Not a production-ready EC2 deployment
- Not a high-availability architecture
- Not hardened beyond lab-level security controls


## ⏱️ Time Investment

- Setup & configuration: ~1 hour
- Troubleshooting IAM & CLI issues: ~1 hour
- Documentation & cleanup: ~1 hour


## ♻️ Reproducibility

This lab can be safely repeated at any time using the documented AWS CLI commands.  
All resources are created explicitly and terminated manually to prevent unintended costs.


## 🏁 Final Notes
This project reflects real-world AWS engineering workflows, including troubleshooting, security enforcement, and cost management. It was intentionally designed to surface and resolve common AWS operational challenges.


## 💼 Professional & Interview Relevance
### Resume Bullet
Provisioned, monitored, and securely decommissioned AWS EC2 infrastructure using AWS CLI (PowerShell), implementing IAM authentication, SSH access, CloudWatch monitoring, and least-privilege security controls.

### Interview Talking Points
- Region-specific AMIs
- IAM permissions vs policies
- CLI vs Console tradeoffs
- Cost control strategies
- Security-first cloud design


## 🚀 Future Enhancements

- Auto Scaling Group (ASG)
- CloudWatch alarms
- Terraform implementation
- GitHub Actions CI/CD
- AWS Systems Manager Session Manager


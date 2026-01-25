# 🔐 Secure Data Storage, Transmission & Digital Signatures (GnuPG)

![Crypto](https://img.shields.io/badge/Cryptography-OpenPGP-success)
![GnuPG](https://img.shields.io/badge/GnuPG-Gpg4win-blue)
![Security](https://img.shields.io/badge/Security-Encryption%20%26%20Signing-critical)
![Standards](https://img.shields.io/badge/Standards-NIST%20CSF%20%7C%20ISO%2027001-informational)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)
![Cloud](https://img.shields.io/badge/Cloud-Azure%20Key%20Vault-blueviolet)

## Portfolio Artifact – Applied Cryptography

This project demonstrates the **real-world application of cryptographic principles**—secure data storage, secure data transmission, and digital signatures—using **GnuPG (Gpg4win)** on a modern Windows platform.

Rather than manually implementing cryptographic algorithms (e.g., DES, RSA, Diffie-Hellman), the lab focuses on **industry-standard, production-aligned practices** using OpenPGP tooling that mirrors how encryption, signing, and key management are handled in **enterprise and cloud security environments**.

> Scope note: This project emphasizes secure configuration, key management, and cryptographic operations rather than algorithm implementation.

---

## What This Demonstrates

- Public-key cryptography using **OpenPGP**
- Digital signatures for **integrity** and **non-repudiation**
- Encryption for **confidentiality**
- Secure private-key handling with **passphrase protection**
- Modern elliptic-curve cryptography (**Curve25519 / EdDSA**)
- Troubleshooting cryptographic failures (e.g., bad passphrase, signing timeouts)

---

## Core Security Principles Demonstrated

| Security Principle | Implementation |
|------------------|----------------|
| Confidentiality | File encryption using OpenPGP |
| Integrity | Digital signatures |
| Authenticity | Identity-bound signing keys |
| Non-repudiation | Signed data verification |
| Key Management | Passphrase-protected private keys |
| Cryptographic Agility | ECC (Curve25519 / EdDSA) |

---

## Explicit Mapping to NIST Cybersecurity Framework (CSF)

### Identify (ID)
- Cryptographic assets (keys, certificates) are clearly identified and managed.
- User identity is explicitly bound to cryptographic material (name and email).

**Relevant controls**
- ID.AM-1 – Physical and logical assets inventoried  
- ID.GV-1 – Governance of cryptographic use established  

---

### Protect (PR)
- Strong encryption applied to data at rest.
- Private keys protected using strong passphrases.
- Modern cryptographic algorithms used (ECC instead of legacy RSA/DES).

**Relevant controls**
- PR.DS-1 – Data protected at rest  
- PR.DS-2 – Data protected in transit  
- PR.AC-1 – Identity-based access control  

---

### Detect (DE)
- Cryptographic failures detected (e.g., incorrect passphrase, signing timeout).
- Verification confirms whether data has been altered or tampered with.

**Relevant controls**
- DE.CM-7 – Monitoring for unauthorized activity  
- DE.DP-4 – Event outcomes validated  

---

### Respond (RS)
- Signing failures analyzed and corrected through configuration and retry.
- Key usage errors remediated without generating insecure cryptographic material.

**Relevant controls**
- RS.AN-1 – Root cause analysis performed  
- RS.MI-1 – Incidents contained and mitigated  

---

### Recover (RC)
- Encrypted data remains recoverable using the correct private key.
- Keys remain valid across sessions and can be restored from backups.

**Relevant controls**
- RC.IM-1 – Recovery plans incorporate cryptographic dependencies  

---

## Mapping to ISO/IEC 27001 (Annex A)

| ISO 27001 Control | Alignment |
|------------------|----------|
| A.8.12 – Data encryption | OpenPGP encryption for stored data |
| A.8.13 – Key management | Secure key generation, passphrases, validity |
| A.5.17 – Authentication information | Identity-bound signing keys |
| A.8.10 – Information deletion | Encrypted data unreadable without keys |
| A.8.9 – Configuration management | Proper cryptographic configuration |

---

## Cloud Security Bridge (Enterprise Equivalents)

Although this lab uses **local OpenPGP**, the cryptographic model directly maps to cloud-native services.

### AWS KMS (Key Management Service)

| OpenPGP Concept | AWS KMS Equivalent |
|---------------|-------------------|
| Private key | Customer Master Key (CMK) |
| Passphrase | IAM policy + key policy |
| File encryption | Envelope encryption |
| Digital signatures | KMS Sign / Verify API |
| Key rotation | Automatic CMK rotation |

---

### Azure Key Vault

| OpenPGP Concept | Azure Key Vault Equivalent |
|---------------|----------------------------|
| Public/private key pair | Key Vault asymmetric key |
| Key validity | Key expiration & rotation |
| Digital signature | Key Vault Sign / Verify |
| Key protection | HSM-backed keys |
| Identity binding | Azure AD / Entra ID |

> **Insight:**  
> This lab demonstrates foundational key lifecycle management skills required before working with AWS KMS, Azure Key Vault, or HashiCorp Vault.

---

## Tools & Technologies

- Gpg4win 4.4.1
- GnuPG (OpenPGP)
- Kleopatra key manager
- Windows OS
- Elliptic Curve Cryptography (ECC)

---

## Implementation Summary

- Installed and configured Gpg4win
- Generated OpenPGP public/private key pair
- Secured private key using a strong passphrase
- Encrypted plaintext files for secure storage
- Digitally signed files to ensure authenticity
- Verified successful encryption and signing operations

---

## Cybersecurity Role Relevance

This project aligns with responsibilities in:

- Cybersecurity Analyst / SOC Analyst
- Cloud Security Engineer
- DevSecOps Engineer
- Information Security / GRC Analyst
- Digital Forensics (foundational)

---

## Why This Project Matters

Modern security professionals **do not implement cryptographic algorithms manually**.  
They **design, configure, validate, and audit secure cryptographic systems**.

This artifact demonstrates:
- Practical cryptography
- Secure key handling
- Identity-based trust models
- Troubleshooting real cryptographic failures
- Audit-ready security operations

---

## Cloud Key Management Extension (Azure Key Vault)

To bridge local cryptographic fundamentals with enterprise cloud security,
this lab was extended using **Azure Key Vault** to demonstrate how modern
cloud platforms manage encryption keys without exposing private material.

> Related project:  
> **Azure Hello World – Static Web App Deployment**  
> (Demonstrates secure-by-default cloud hosting and CI/CD governance)

### What Was Implemented

- Provisioned Azure Key Vault via Azure CLI
- Generated a non-exportable RSA key (RSA-OAEP)
- Enforced RBAC using **Key Vault Crypto Officer**
- Performed encryption and decryption operations via CLI
- Verified plaintext recovery without accessing private keys

### Security Principles Demonstrated

| Principle | Implementation |
|--------|----------------|
| Key Isolation | Private keys never leave Azure Key Vault |
| Least Privilege | RBAC-enforced cryptographic permissions |
| Confidentiality | Data encrypted using managed asymmetric keys |
| Auditability | All operations logged by Azure |

### Mapping to OpenPGP Concepts

| OpenPGP | Azure Key Vault |
|------|----------------|
| Private key | Non-exportable Key Vault key |
| Passphrase | Azure RBAC + Entra ID |
| Sign / Verify | Key Vault Sign / Verify |
| Encrypt / Decrypt | Key Vault Encrypt / Decrypt |

> **Result:**  
> This extension demonstrates how foundational cryptography skills
> translate directly into cloud-native key management services
> such as Azure Key Vault and AWS KMS.

### Verification Evidence
- Successful encryption and decryption operations were verified using Azure Key Vault CLI, with private key material remaining non-exportable and inaccessible.

### Conceptual Architecture Diagram

```text
┌──────────────────────────────┐
│        OpenPGP (Local)       │
└──────────────────────────────┘
        │
        │ 1. Generate Key Pair
        ▼
┌──────────────────────────────┐
│ Public Key  | Private Key    │
│ (Shared)    | (Local, Encrypted
│             |  w/ Passphrase)│
└──────────────────────────────┘
        │
        │ 2. Encrypt / Sign
        ▼
┌──────────────────────────────┐
│ Encrypted + Signed Data      │
│ (.gpg file)                  │
└──────────────────────────────┘
        │
        │ 3. Decrypt / Verify
        ▼
┌──────────────────────────────┐
│ Plaintext (Integrity Verified)│
└──────────────────────────────┘
```

```text
┌────────────────────────────────────────┐
│        Azure Key Vault (Cloud)          │
└────────────────────────────────────────┘
        │
        │ 1. Create Non-Exportable Key
        ▼
┌────────────────────────────────────────┐
│ Azure Key Vault                         │
│ ─ RSA Key (HSM / Software Protected)   │
│ ─ Private Key NEVER Exposed            │
└────────────────────────────────────────┘
        │
        │ 2. Encrypt / Decrypt via API
        ▼
┌────────────────────────────────────────┐
│ Ciphertext returned to application     │
│ (Base64 encoded)                       │
└────────────────────────────────────────┘
        │
        │ 3. Decrypt (Authorized Only)
        ▼
┌────────────────────────────────────────┐
│ Plaintext (Access controlled by RBAC)  │
└────────────────────────────────────────┘
```

These diagrams highlight the architectural evolution from local cryptographic key ownership (OpenPGP) to cloud-native key isolation (Azure Key Vault).
While OpenPGP secures data through locally managed private keys and passphrases, Azure Key Vault enforces cryptographic operations through identity-based access control and non-exportable keys—eliminating private key exposure.
This comparison demonstrates how foundational cryptography skills translate directly into enterprise cloud security architectures.

## 🔍 Threat Considerations (High-Level, Practical)

- Private key compromise mitigated via non-exportable keys (Key Vault)
- Unauthorized encryption attempts blocked by RBAC
- Replay and tampering mitigated via asymmetric cryptography
- Accidental data exposure reduced through encryption at rest

---

## 📌 Resume Bullet

> Implemented secure data storage, encrypted transmission, and digital signatures using OpenPGP (GnuPG/Gpg4win), applying public-key cryptography, key management, and integrity controls aligned with NIST CSF and ISO/IEC 27001.

---

## Recommended Repository Structure

```text
applied-cryptography-openpgp/
├── README.md
├── lab-report/
│   └── final-lab-report.pdf
├── screenshots/
│   ├── key-generation.png
│   ├── encryption-success.png
│   └── signature-verification.png
├── samples/
│   ├── secure-message.txt
│   └── secure-message.txt.gpg
└── notes/
    └── nist-iso-mapping.md
```

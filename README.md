# 📊 Early Risk Signals – Credit Card Delinquency Monitoring Platform

*A Machine-Learning–Driven Early Warning System with Real-Time Behavioral Analytics & WhatsApp-Based Interventions*

This project implements a **full-stack early risk detection platform** designed to identify **emerging credit card delinquency signals** using a combination of behavioral analytics, machine learning, and automated WhatsApp-based communication.

It consists of:

* 🧠 **ML Engine** — computes behavioural features and risk band predictions (L/M/H)
* 🔐 **FastAPI Backend** — orchestrates scoring, authentication, and alert workflows
* 🎨 **React Frontend** — modern user and admin dashboards
* 🗄️ **MongoDB Database** — flexible NoSQL storage
* 💬 **WhatsApp Business API** — OTP onboarding, welcome messages, and risk alerts
* 🧮 **Rule Engine** — overrides or supplements ML insights with expert rules

This platform demonstrates how **real-time behavioural monitoring** can drastically improve early detection of financial stress and reduce credit losses.

---

# 🧭 Table of Contents

1. [Features](#-features)
2. [System Architecture](#-system-architecture)
3. [Machine Learning Engine Overview](#-machine-learning-engine-overview)
4. [How the Model Predicts Risk Bands](#-how-the-risk-model-predicts-l--m--h)
5. [Tech Stack](#-tech-stack)
6. [Repository Structure](#-repository-structure)
7. [Backend Setup](#-backend-setup-local)
8. [Frontend Setup](#-frontend-setup-local)
9. [Docker + AWS Deployment Guide](#-docker--aws-deployment)
10. [WhatsApp Integration](#-whatsapp-integration)
11. [Future Enhancements](#-future-enhancements)

---

# 🚀 Features

### 🔐 1. WhatsApp-Based Authentication

* OTP-based signup (no passwords)
* First-login welcome message
* JWT authentication for secure sessions

### 📉 2. Real-Time Early Risk Scoring

* Behavioural aggregates updated per transaction
* Ensemble ML scoring (LR + Decision Tree + Rules)
* Risk band assignment: **Low / Medium / High**
* SHAP explanations for model transparency

### 📲 3. Automated WhatsApp Alerts

* High-risk detection alerts
* Admin-triggered customer alerts
* WhatsApp template support

### 📊 4. Admin Dashboard

* Portfolio risk distribution
* View top high-risk accounts
* Customer drilldown
* Edit behavioural features
* Transaction histories
* One-click WhatsApp warning button

### 👤 5. User Dashboard

* View credit usage and risk status
* Get alerts in WhatsApp
* Add transactions (demo mode)

---

# 🏗️ System Architecture

```
Frontend (React)
    ↑            ↓
    └──JWT────→ FastAPI Backend
                     ↓
             ML Risk Engine (LR + Tree + Rules)
                     ↓
                 MongoDB
                     ↓
            WhatsApp Business API
```

**Key components:**

* **Frontend:** React SPA for user/admin UIs
* **Backend:** FastAPI orchestrates authentication, ML scoring, alerts
* **Data Store:** MongoDB with collections for users, transactions, scores, OTPs
* **Messaging:** WhatsApp API for two-way communication
* **ML Engine:** Logistic regression + decision tree + rule engine

---

# 🧠 Machine Learning Engine Overview

The ML engine combines **statistical modeling**, **supervised learning**, and **business rules** to detect emerging credit stress.

### 📂 1. Input Behavioural Features

Examples:

| Feature              | Description                              |
| -------------------- | ---------------------------------------- |
| UtilisationPct       | How much of credit limit is used         |
| MerchantMixIndex     | Diversity of merchants spent at          |
| CashWithdrawalPct    | Share of cash withdrawals (high → risky) |
| RecentSpendChangePct | Sudden increase in spending              |
| MinDuePaidFrequency  | Frequency of only paying minimum amounts |
| AvgPaymentRatio      | Repayment behavior                       |

Features are recomputed whenever a new transaction enters the system.

---

# 🎛️ How the Risk Model Predicts L / M / H

The platform uses a **three-stage ML pipeline**:

---

## **Stage 1 — Logistic Regression Model**

A trained Scikit-Learn logistic regression model outputs:

* `ml_probability` → estimated delinquency probability
* Uses standardised behavioural features
* Advantages: Explainable weights, fast inference

Example output:
`0.78` = 78% risk (High)

---

## **Stage 2 — Decision Tree Model**

A lightweight decision tree captures **nonlinear interactions** the LR model may miss.

Example rule:

```
IF UtilisationPct > 85% AND RecentSpendChangePct > 40%
   THEN High Risk
```

The tree outputs a probability or class.

---

## **Stage 3 — Rule Engine Overrides**

Some patterns must always trigger elevation:

| Rule                            | Reason                              |
| ------------------------------- | ----------------------------------- |
| CashWithdrawalPct > 40%         | Sign of liquidity crisis            |
| 3+ consecutive minimum payments | High distress risk                  |
| Utilisation ≥ 95%               | Maxed-out card → likely delinquency |

Rules apply deterministic overrides such as:

```
IF rule flags "critical" → set risk_band = High
```

---

## 📘 Final Band Assignment

```
IF ensemble_probability < 0.33 → LOW
IF ensemble_probability < 0.66 → MEDIUM
ELSE → HIGH
```

This combines:

```
ensemble = (LR + Tree) / 2 ± Rule Adjustments
```

Every score is logged into `risk_scores` for audit and tracking.

---

# 💻 Tech Stack

### **Backend**

* FastAPI
* Python 3.11
* MongoDB (PyMongo)
* Scikit-learn
* SHAP explainers
* Pydantic v2
* Uvicorn
* WhatsApp Cloud API

### **Frontend**

* React + Vite
* Axios
* Context API for auth
* Custom component library

### **Infrastructure**

* Docker
* AWS EC2
* AWS ECR
* NGINX (frontend hosting)

---

# 📁 Repository Structure

```
backend/
  app/
    core/        # config, db, security
    routers/     # auth, admin, risk, whatsapp
    services/    # ML service, whatsapp service
    ml/          # ML models & pipelines
    models/      # Mongo models
    schemas/
    main.py
  artifacts/     # .pkl, .pt, SHAP, scaler files
  Dockerfile

frontend/
  src/           # Pages, components, auth context
  public/
  Dockerfile

environment_backend.yml
README.md
```

---

# 🛠 Backend Setup (Local)

```bash
conda env create -f environment_backend.yml
conda activate credit-risk
cd backend
uvicorn app.main:app --reload
```

---

# 🎨 Frontend Setup (Local)

```bash
cd frontend
npm install
npm run dev
```

---

# 🐳 Docker & AWS Deployment

## 1. Login to AWS ECR

```bash
aws ecr get-login-password --region ap-south-1 \
| docker login --username AWS --password-stdin 077540773844.dkr.ecr.ap-south-1.amazonaws.com
```

## 2. Build Images

```bash
docker build -t montukr/credit-card-risk-backend ./backend
docker build -t montukr/credit-card-risk-frontend ./frontend
```

## 3. Tag and Push

```bash
docker tag montukr/credit-card-risk-backend:latest \
077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest

docker push 077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest
```

Same for frontend.

## 4. Run on EC2

Backend:

```bash
docker run -d -p 8000:8000 \
--env-file .env \
montukr/credit-card-risk-backend
```

Frontend (NGINX):

```bash
docker run -d -p 80:80 montukr/credit-card-risk-frontend
```

---

# 💬 WhatsApp Integration

### Supports:

* OTP for login
* Welcome messages
* Automated risk alerts
* Admin-triggered alerts

Requires approved templates like:

```
welcome_user
risk_high_alert
```

---

# 🔭 Future Enhancements

* Multi-language WhatsApp templates
* Integration with credit bureaus
* Real-time streaming via Kafka
* Gradient Boosting or XGBoost risk models
* Dashboard analytics using Apache Superset
* Automated repayment plan recommendations

---

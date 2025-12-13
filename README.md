# 📊 Early Risk Signals – Credit Card Delinquency Monitoring Platform

*A Machine-Learning–Driven Early Warning System with Real-Time Behavioral Analytics & WhatsApp-Based Interventions*

## 🔗 Live Demo

Web app (Frontend): http://13.205.19.249/
 
Backend API: http://13.200.50.168:8000/docs

Test Username / Password:  
- Admin: admin / 1234  
- User 1: test1 / 1234
- User 2: test2 / 1234


This project implements a **full-stack early risk detection platform** designed to identify **emerging credit card delinquency signals** using a combination of behavioral analytics, machine learning, and automated WhatsApp-based communication.

It consists of:

* 🧠 **ML Engine** — behavioural scoring + risk band prediction
* 🔐 **FastAPI Backend** — authentication, ML inference, workflows
* 🎨 **React Frontend** — dashboards for customers & admins
* 🗄️ **MongoDB Database** — users, transactions, features, OTPs
* 💬 **WhatsApp Business API** — OTP login & risk alerts
* ⚖️ **Rule Engine** — deterministic overrides for critical scenarios

This platform demonstrates how **real-time behavioural monitoring** can significantly improve early detection of financial stress and reduce credit losses.

---

# 🧭 Table of Contents

1. [Features](#-features)
2. [System Architecture](#-system-architecture)
3. [Machine Learning Engine Overview](#-machine-learning-engine-overview)
4. [How the Risk Model Predicts L / M / H](#-how-the-risk-model-predicts-l--m--h)
5. [Tech Stack](#-tech-stack)
6. [Repository Structure](#-repository-structure)
7. [.env Configuration](#-env-configuration)
8. [Backend Setup](#-backend-setup-local)
9. [Frontend Setup](#-frontend-setup-local)
10. [Docker + AWS Deployment](#-docker--aws-deployment)
11. [WhatsApp Integration](#-whatsapp-integration)
12. [Future Enhancements](#-future-enhancements)

---

# 🚀 Features

### 🔐 1. WhatsApp-Based Authentication

* OTP-based registration and login
* Seamless onboarding
* Automatic first-login welcome message

### 📉 2. Real-Time Early Risk Scoring

* Behavioural aggregation per transaction
* Ensemble ML scoring (Logistic Regression + Decision Tree)
* Risk band: **Low / Medium / High**
* SHAP explanations for transparency

### 📲 3. Automated WhatsApp Alerts

* High-risk detection alerts
* Admin-triggered warnings
* Template-driven notifications

### 📊 4. Admin Dashboard

* Portfolio-level risk distribution
* Top high-risk customers
* Customer transaction/risk history
* Trigger alerts instantly

### 👤 5. Customer Dashboard

* Credit usage summary
* Risk band overview
* Real-time alerts via WhatsApp

---

# 🏗️ System Architecture

```
Frontend (React)
        ↑    ↓
        └ JWT ────→  FastAPI Backend
                          ↓
                   ML Risk Engine
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

# 🧠 Machine Learning Engine Overview (Short Version)

The ML engine computes early risk signals by processing **behavioural features** derived from customer transactions.

### Key input features include:

* **UtilisationPct**
* **CashWithdrawalPct**
* **RecentSpendChangePct**
* **MerchantMixIndex**
* **PaymentRatio**, **MinDueFrequency**

Every transaction updates these aggregates, triggering re-scoring when thresholds change.

The ML engine consists of:

1. **Logistic Regression Model** (probability-based, interpretable)
2. **Decision Tree Classifier** (nonlinear pattern detection)
3. **Rule Engine** (hard overrides such as ≥95% utilisation or >40% cash usage)

---

# 🎛️ How the Risk Model Predicts L / M / H (Short Version)

1. **Logistic Regression** produces a baseline delinquency probability.
2. **Decision Tree** identifies non-linear high-risk cases (spend spikes, cash patterns).
3. **Rule Engine** enforces deterministic red flags (e.g., 3+ minimum payments → High).
4. Final score is averaged and adjusted:

```
IF score < 0.33 → LOW
IF score < 0.66 → MEDIUM
ELSE → HIGH
```

This ensures **explainability + sensitivity to risky behaviour**.

---

# 💻 Tech Stack

### Backend

FastAPI · Python 3.11 · MongoDB · Scikit-Learn · SHAP · Pydantic v2 · WhatsApp Cloud API

### Frontend

React · Vite · Axios · Context API

### Infrastructure

Docker · AWS EC2 · AWS ECR · NGINX

---

# 📁 Repository Structure

```
backend/
  app/
    core/
    routers/
    services/
    ml/
    models/
    schemas/
    main.py
  artifacts/
  Dockerfile
frontend/
  src/
  public/
  Dockerfile
environment_backend.yml
README.md
```

---

# 🔐 .env Configuration

## 1. Backend — `.env.example`

Create:

```
backend/.env.example
```

```env
# ==== App ====
APP_NAME="Credit Risk Platform"

# ==== MongoDB ====
MONGODB_URI="mongodb://localhost:27017"
MONGODB_DB="credit_risk"

# ==== JWT ====
JWT_SECRET_KEY="CHANGE_ME"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ==== Artifacts ====
ARTIFACTS_DIR="artifacts"

# ==== WhatsApp API ====
WHATSAPP_TOKEN=""
WHATSAPP_PHONE_ID=""
WHATSAPP_API_VERSION="v21.0"

WHATSAPP_TEMPLATE_WELCOME=""
WHATSAPP_TEMPLATE_FLAGGED=""
```

---

## 2. Frontend — `.env.example`

```
VITE_API_BASE_URL="http://localhost:8000"
VITE_API_URL="http://<BACKEND_ELASTIC_IP>:8000"
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

# 🐳 Docker + AWS Deployment

## 1. Authenticate with ECR

```bash
aws ecr get-login-password --region ap-south-1 \
| docker login --username AWS --password-stdin 077540773844.dkr.ecr.ap-south-1.amazonaws.com
```

---

## 2. Build images

```bash
docker build -t montukr/credit-card-risk-backend ./backend
docker build -t montukr/credit-card-risk-frontend ./frontend
```

---

## 3. Tag & Push (Backend)

```bash
docker tag montukr/credit-card-risk-backend:latest \
077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest

docker push \
077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest
```

Repeat for frontend.

---

## 4. Run Containers on EC2

### Backend

```bash
docker run -d -p 8000:8000 \
--env-file /home/ubuntu/backend.env \
montukr/credit-card-risk-backend
```

### Frontend (NGINX)

```bash
docker run -d -p 80:80 montukr/credit-card-risk-frontend
```

---

# 💬 WhatsApp Integration

Supports:

* OTP onboarding
* Welcome messages at first login
* Automatic High-Risk alerts
* Admin-triggered alerts

Templates must be approved in Meta WhatsApp Cloud API dashboard.

---

# 🔭 Future Enhancements

* Multi-language templates
* Integration with bureaus / alternate data sources
* Gradient boosting / deep models
* Kafka-based streaming
* Personalized repayment suggestions

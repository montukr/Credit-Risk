# Credit Card Risk – AWS Deployment Guide

This guide details the step-by-step process to deploy the **Credit Risk Platform** on AWS EC2 using Docker and AWS ECR.

## 🏗️ Architecture

  * **Backend:** FastAPI (Python 3.11/Conda) running on an `x86` EC2 instance.
  * **Frontend:** React (Vite) served via Nginx running on a separate `x86` EC2 instance.
  * **Registry:** AWS Elastic Container Registry (ECR).
  * **Persistence:** MongoDB Atlas (Cloud).
  * **Automation:** Systemd services for auto-restart on reboot.

-----

## 🧱 Prerequisites

Ensure the following are installed on your local machine:

  * [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  * [AWS CLI](https://aws.amazon.com/cli/)
  * [Git](https://git-scm.com/)

Configure your AWS CLI:

```bash
aws configure
# Enter your Access Key, Secret Key, Region (ap-south-1), and format (json)
```

-----

## 📂 1. Docker Configuration

Ensure your local repository has the following Dockerfiles set up.

### 🐍 Backend Dockerfile

**File:** `backend/Dockerfile`

```dockerfile
FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# ✅ FIX: Install system build tools (Make Docker "Rich" for Cryptography/JWT)
# - build-essential: provides gcc/make for compiling C extensions
# - libssl-dev: required for cryptography/python-jose
# - libffi-dev: required for cffi
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY environment_backend.yml /tmp/environment_backend.yml

# Create conda environment
RUN conda env create -f /tmp/environment_backend.yml && \
    conda clean -afy

# Activate conda for subsequent commands
SHELL ["bash", "-lc"]

# Set PATH for the created environment
ENV CONDA_DEFAULT_ENV=credit-risk
ENV PATH=/opt/conda/envs/credit-risk/bin:$PATH

# Copy application code
COPY app /app/app

# Expose FastAPI port
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ⚛️ Frontend Dockerfile

**File:** `frontend/Dockerfile`

```dockerfile
# 1) Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# 2) Nginx serve stage
FROM nginx:1.27-alpine

# Remove default nginx static content
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Create Nginx config for React Router (SPA) support
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

-----

## 🚀 Phase 1: Build & Push Backend

1.  **Login to ECR:**

    ```bash
    aws ecr get-login-password --region ap-south-1 | \
      docker login --username AWS --password-stdin 077540773844.dkr.ecr.ap-south-1.amazonaws.com
    ```

2.  **Build & Push (x86 Platform):**
    *Note: The `--platform linux/amd64` flag is critical if building from a Mac (M1/M2/M3) to ensure compatibility with standard EC2 instances.*

    ```bash
    cd backend

    docker buildx build \
      --platform linux/amd64 \
      -t 077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest \
      --push .
    ```

-----

## 🖥️ Phase 2: Backend EC2 Deployment

### 2.1 Launch Instance

  * **AMI:** Amazon Linux 2023 (x86\_64)
  * **Type:** `t3.medium` (Recommended for ML workloads)
  * **Security Group:** Allow SSH (22) and Custom TCP (8000).
  * **Elastic IP:** Allocate an IP (e.g., `45.204.xxx.xxx`) and associate it with this instance.

### 2.2 Setup Environment

SSH into the Backend EC2:

```bash
ssh -i your-key.pem ec2-user@<BACKEND_ELASTIC_IP>
```

Install Docker:

```bash
sudo yum update -y
sudo yum install -y docker awscli
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
```

*Tip: Log out (`exit`) and log back in for group permissions to take effect.*

### 2.3 Deploy Container

1.  **Login to ECR:**

    ```bash
    aws ecr get-login-password --region ap-south-1 | \
      docker login --username AWS --password-stdin 077540773844.dkr.ecr.ap-south-1.amazonaws.com
    ```

2.  **Pull Image:**

    ```bash
    docker pull 077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest
    ```

3.  **Create `.env` File:**

    ```bash
    sudo mkdir -p /opt/credit-risk-backend
    sudo chown ec2-user:ec2-user /opt/credit-risk-backend
    nano /opt/credit-risk-backend/.env
    ```

    **Paste the following configuration:**
    *(Replace sensitive values if necessary)*

    ```properties
    # ==== App ====
    APP_NAME=Credit Risk Platform

    # ==== MongoDB ====
    # Atlas MongoDB for Docker
    MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/
    MONGODB_DB=credit_risk

    # ==== CORS ORIGINS ====
    # Add your Frontend IP here once created
    CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://13.205.19.249

    # ==== JWT ====
    JWT_SECRET_KEY=change_this_to_a_long_random_secret
    JWT_ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=720

    # ==== Artifacts ====
    ARTIFACTS_DIR=artifacts

    # ==== WhatsApp ====
    WHATSAPP_TOKEN=
    WHATSAPP_PHONE_ID=
    WHATSAPP_API_VERSION=v21.0
    WHATSAPP_TEMPLATE_WELCOME=welcome_user_alert
    WHATSAPP_TEMPLATE_FLAGGED=flagged_risk_alert
    ```

4.  **Run Container:**

    ```bash
    docker run -d --name credit-backend \
      --env-file /opt/credit-risk-backend/.env \
      -p 8000:8000 \
      077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-backend:latest
    ```

-----

## 🌐 Phase 3: Build & Push Frontend

1.  **Configure Production API URL:**
    Locally, create or edit `frontend/.env.production`:

    ```properties
    VITE_API_URL=http://<BACKEND_ELASTIC_IP>:8000
    ```

2.  **Build & Push (x86 Platform):**

    ```bash
    cd frontend

    docker buildx build \
      --platform linux/amd64 \
      -t 077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-frontend:latest \
      --push .
    ```

-----

## 🖥️ Phase 4: Frontend EC2 Deployment

### 4.1 Launch Instance

  * **AMI:** Amazon Linux 2023 (x86\_64)
  * **Type:** `t3.micro`
  * **Security Group:** Allow SSH (22) and HTTP (80).
  * **Elastic IP:** Allocate an IP (e.g., `15.235.xxx.xxx`) and associate it with this instance.

### 4.2 Setup & Deploy

SSH into the Frontend EC2:

```bash
ssh -i your-key.pem ec2-user@<FRONTEND_ELASTIC_IP>
```

Install Docker (same steps as Backend).

**Deploy Container:**

```bash
# Login
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin 077540773844.dkr.ecr.ap-south-1.amazonaws.com

# Pull
docker pull 077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-frontend:latest

# Run (Port 80)
docker run -d --name credit-frontend \
  -p 80:80 \
  077540773844.dkr.ecr.ap-south-1.amazonaws.com/montukr/credit-card-risk-frontend:latest
```

-----

## 🔗 Phase 5: Configure CORS

**Critical Step:** Now that you have the **Frontend IP**, you must update the Backend to allow requests from it.

1.  SSH back into the **Backend EC2**.
2.  Edit the environment file:
    ```bash
    nano /opt/credit-risk-backend/.env
    ```
3.  Update the `CORS_ORIGINS` line:
    ```properties
    CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://<FRONTEND_ELASTIC_IP>
    ```
4.  Restart the Backend container:
    ```bash
    docker stop credit-backend
    docker rm credit-backend
    # Run the start command from Phase 2.3 again
    ```

-----

## 🔄 Phase 6: Auto-Start Services (Systemd)

To ensure your containers restart automatically if the EC2 reboots, set up Systemd services.

### Backend Service (Run on Backend EC2)

```bash
sudo nano /etc/systemd/system/credit-backend.service
```

Paste configuration:

```ini
[Unit]
Description=Credit Risk Backend - Restart Existing Container on Boot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker start credit-backend
ExecStop=/usr/bin/docker stop credit-backend
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable credit-backend
sudo systemctl start credit-backend
```

### Frontend Service (Run on Frontend EC2)

Repeat the steps above but name the file `credit-frontend.service` and change `credit-backend` to `credit-frontend`.

-----

## 🎉 Deployment Complete

  * **Backend API Docs:** `http://<BACKEND_ELASTIC_IP>:8000/docs`
  * **Frontend Application:** `http://<FRONTEND_ELASTIC_IP>`
# Cloud Financial Risk Analysis API

A cloud-based financial risk analysis application combining **Google App Engine, AWS Lambda, Amazon EC2 and Amazon S3** to analyse historical market data, evaluate trading signals and estimate financial risk using **Monte Carlo simulation**.

> **MSc Cloud Computing Project — University of Surrey**

---

## 📌 Overview

This project implements a **Flask-based REST API** for analysing historical Amazon (AMZN) market data and evaluating trading signals using statistical simulation.

The application supports two cloud-based compute approaches — **AWS Lambda and Amazon EC2** — allowing analysis workloads to be executed using different compute models. Results and audit information are stored in **Amazon S3**, while the application provides endpoints for resource initialisation, readiness checks, analysis, cost estimation, result retrieval and resource termination.

The project demonstrates the design and implementation of a **multi-cloud application architecture** combining managed application hosting, serverless computing, virtual-machine-based computation and cloud storage.

---

## 🏗️ Architecture

```text
                         Client
                           │
                           ▼
                ┌─────────────────────┐
                │  Google App Engine  │
                │     Flask API       │
                └──────────┬──────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      ┌──────────────┐           ┌──────────────┐
      │ AWS Lambda   │           │   AWS EC2    │
      │  Serverless  │           │ Cloud Compute│
      └──────┬───────┘           └──────┬───────┘
             │                          │
             └────────────┬─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │    AWS S3    │
                   │ Results &    │
                   │ Audit Data   │
                   └──────────────┘
```

### **Architecture Components**

| **Component** | **Purpose** |
|---|---|
| **Google App Engine** | Hosts the Flask REST API |
| **AWS Lambda** | Provides serverless execution for analysis and cloud-management operations |
| **Amazon EC2** | Provides VM-based compute for analysis workloads |
| **Amazon S3** | Stores analysis results, audit information and generated charts |
| **AWS Systems Manager** | Supports remote execution and management of EC2 analysis workloads |
| **AWS Cost Explorer** | Provides cloud-cost information for resource usage analysis |

---

## 🔄 Request Flow

The application follows a cloud-based workflow for executing and retrieving financial analysis.

```text
                           Client
                             │
                             ▼
                    ┌─────────────────┐
                    │   Flask REST    │
                    │       API       │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
          ┌──────────────┐        ┌──────────────┐
          │ AWS Lambda   │        │   AWS EC2    │
          │   Analysis   │        │   Analysis   │
          └──────┬───────┘        └──────┬───────┘
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │   AWS S3    │
                      │             │
                      │ • Results   │
                      │ • Audit     │
                      │ • Charts    │
                      └──────┬──────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Flask API    │
                    └────────┬────────┘
                             │
                             ▼
                           Client
```

### **Workflow**

1. The client sends an analysis or resource-management request to the Flask API.
2. The application initialises either **AWS Lambda or Amazon EC2** compute resources.
3. Historical market data is retrieved and processed.
4. Trading signals are generated from the market data.
5. Monte Carlo simulations are executed using the selected compute service.
6. Risk and profit/loss results are generated.
7. Results and audit information are stored in **Amazon S3**.
8. The API provides endpoints for retrieving analysis results, charts, execution information and audit data.
9. Cloud resources can be monitored and terminated when they are no longer required.

---

## ✨ Key Features

- **Flask REST API** for financial analysis and cloud resource management
- Historical market-data retrieval using **Yahoo Finance**
- Trading signal identification based on price movements
- **Monte Carlo simulation** for financial risk analysis
- **95% and 99% Value at Risk (VaR)** calculations
- Profit/loss calculation based on trading signals
- **AWS Lambda-based analysis**
- **AWS EC2-based analysis**
- Dynamic EC2 instance provisioning
- EC2 readiness monitoring
- EC2 termination monitoring
- **Amazon S3** storage for analysis and audit information
- Analysis chart generation and S3 storage
- Execution time measurement
- Cloud cost estimation
- Audit logging of analysis parameters and results
- Concurrent Lambda invocations using Python's `ThreadPoolExecutor`

---

## 📊 Financial Analysis

The application retrieves historical **Amazon (AMZN)** market data and processes the resulting time-series data to identify trading signals and estimate financial risk.

### **Analysis Workflow**

```text
Historical AMZN Market Data
            │
            ▼
     Data Processing
            │
            ▼
 Trading Signal Identification
            │
       ┌────┴────┐
       ▼         ▼
     BUY       SELL
    Signals    Signals
       │         │
       └────┬────┘
            │
            ▼
   Monte Carlo Simulation
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
   VaR 95% VaR 99% P/L
      │     │     │
      └─────┼─────┘
            │
            ▼
     Results & Charts
```

### **Analysis Includes**

- Historical market returns
- Trading signal identification
- Monte Carlo simulation
- **95% Value at Risk**
- **99% Value at Risk**
- Profit/loss analysis
- Execution-time measurement
- Compute-cost estimation
- Result visualisation

The number of simulations, historical analysis period, transaction type and future checking period can be supplied through the API.

---

## ☁️ Cloud Computing

The project uses different cloud services for different parts of the workload.

### **Google App Engine**

Google App Engine provides the hosted application layer and exposes the **Flask REST API** to clients.

### **AWS Lambda**

AWS Lambda provides **serverless execution** for analysis and cloud-management operations.

The application can execute multiple Lambda-based analysis tasks concurrently using Python's `ThreadPoolExecutor`.

### **Amazon EC2**

Amazon EC2 provides **virtual-machine-based compute** for analysis workloads.

The application supports:

- EC2 instance provisioning
- Instance readiness checks
- Analysis execution
- Instance status monitoring
- Resource termination

### **Amazon S3**

Amazon S3 provides persistent storage for:

- Analysis inputs and outputs
- Audit information
- Generated charts
- Analysis result data

### **AWS Systems Manager**

AWS Systems Manager supports **remote execution and management of analysis workloads on EC2 instances**.

### **AWS Cost Explorer**

AWS Cost Explorer is incorporated to retrieve **cloud-cost information** and support analysis of resource usage and associated costs.

---

## 🔌 API

The Flask application exposes REST endpoints covering the main stages of the workflow.

| **Endpoint** | **Method** | **Purpose** |
|---|---|---|
| `/warmup` | `POST` | Initialise Lambda or EC2 compute resources |
| `/scaled_ready` | `GET` | Check compute-resource readiness |
| `/get_warmup_cost` | `GET` | Retrieve warm-up cost information |
| `/analyse` | `POST` | Execute financial analysis |
| `/get_sig_vars9599` | `GET` | Retrieve individual VaR results |
| `/get_avg_vars9599` | `GET` | Retrieve average VaR results |
| `/get_sig_profit_loss` | `GET` | Retrieve individual profit/loss results |
| `/get_tot_profit_loss` | `GET` | Retrieve total profit/loss |
| `/get_chart_url` | `GET` | Generate and retrieve an analysis chart URL |
| `/get_time_cost` | `GET` | Retrieve execution time and cost information |
| `/get_audit` | `GET` | Retrieve audit information |
| `/reset` | `GET` | Reset stored analysis results |
| `/terminate` | `GET` | Terminate active compute resources |
| `/scaled_terminated` | `GET` | Check resource termination status |

---

## 🛠️ Technology Stack

### **Application & Backend**

- **Python**
- **Flask**
- **Gunicorn**
- REST APIs
- JSON

### **Data & Financial Analysis**

- **Pandas**
- **NumPy**
- **SciPy**
- **Matplotlib**
- **yfinance**
- Monte Carlo simulation
- Statistical analysis
- Value at Risk

### **Cloud Technologies**

- **Google App Engine**
- **AWS Lambda**
- **Amazon EC2**
- **Amazon S3**
- **AWS Systems Manager**
- **AWS Cost Explorer**

### **Development & Integration**

- **Boto3**
- REST API integration
- Environment-based configuration
- Python `ThreadPoolExecutor`
- Cloud resource management

---

## 📁 Project Structure

```text
cloud-financial-risk-api/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── index.py
├── analyse.py
├── analyse_api.py
├── analyse_ec2.py
├── audit.py
├── charturl.py
├── ec2_analysis.py
├── reset.py
├── run_analysis.py
├── s3buckfetch.py
├── scaledready.py
├── scaledterminated.py
├── shell_ec2_analysis.py
├── terminate.py
├── Warmup.py
└── warmupcost.py
```

### **Main Components**

| **File** | **Responsibility** |
|---|---|
| `index.py` | Main Flask API and application workflow |
| `analyse.py` | Lambda-based analysis workflow |
| `analyse_api.py` | Financial analysis and Monte Carlo processing |
| `analyse_ec2.py` | Coordinates analysis across EC2 instances |
| `ec2_analysis.py` | EC2-side analysis functionality |
| `run_analysis.py` | Executes analysis workloads on EC2 |
| `Warmup.py` | Provisions EC2 resources |
| `scaledready.py` | Checks EC2 readiness |
| `scaledterminated.py` | Checks resource termination status |
| `terminate.py` | Terminates EC2 resources |
| `audit.py` | Retrieves stored audit information |
| `charturl.py` | Stores generated chart data in S3 |
| `s3buckfetch.py` | Retrieves analysis results from S3 |
| `warmupcost.py` | Retrieves cloud-cost information |
| `reset.py` | Resets stored analysis data |
| `shell_ec2_analysis.py` | Prepares an EC2 environment for analysis |

---

## 🔐 Configuration

Cloud credentials and environment-specific configuration are **not stored in this repository**.

Create a local `.env` file based on `.env.example` and configure the required AWS credentials and environment variables for your own deployment.

### **Example Configuration**

```text
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=your_region
```

> ⚠️ **Security:** Never commit access keys, secret keys, session tokens, private keys or other credentials to GitHub.

Deployment-specific configuration files containing credentials are intentionally excluded from the repository.

---

## 🚀 Running Locally

### **1. Clone the Repository**

```bash
git clone https://github.com/kishore-krishna-srinivasan/cloud-financial-risk-api.git
cd cloud-financial-risk-api
```

### **2. Create a Virtual Environment**

```bash
python -m venv venv
```

### **3. Activate the Environment**

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### **4. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **5. Configure Environment Variables**

Create a local `.env` file and provide the required cloud configuration.

### **6. Start the Flask Application**

```bash
python index.py
```

The application will be available locally at:

```text
http://localhost:5000
```

---

## 🧪 Example Analysis Request

The `/analyse` endpoint accepts analysis parameters through a JSON request.

### **Example**

```bash
curl -X POST http://localhost:5000/analyse \
  -H "Content-Type: application/json" \
  -d '{"h": 101, "d": 10000, "t": "buy", "p": 7}'
```

The resulting analysis can then be accessed through the relevant API endpoints for:

- **Value at Risk**
- **Profit/loss**
- **Charts**
- **Execution time**
- **Cost information**
- **Audit information**

---

## 💡 Engineering Highlights

This project provided practical experience in:

- Designing a **multi-cloud application architecture**
- Building REST APIs with **Flask**
- Integrating AWS services programmatically using **Boto3**
- Working with **serverless and VM-based compute models**
- Managing cloud resources through application code
- Provisioning and terminating EC2 instances programmatically
- Parallelising independent Lambda invocations
- Working with financial time-series data
- Applying **Monte Carlo simulation** to financial risk analysis
- Calculating **Value at Risk**
- Persisting analysis and audit information in cloud storage
- Generating and storing analysis visualisations
- Measuring execution time and estimating cloud costs
- Implementing cloud-resource lifecycle management

---

## 🎯 What This Project Demonstrates

The project brings together several areas of software and data engineering.

### **Software Engineering**

REST API development, backend application logic, cloud-service integration and resource management.

### **Data & Analytics**

Financial time-series processing, trading-signal analysis, statistical simulation and risk estimation.

### **Cloud Engineering**

Multi-cloud deployment, serverless computing, virtual-machine-based workloads, object storage and cloud resource lifecycle management.

### **Financial Analysis**

Monte Carlo simulation, Value at Risk, profit/loss analysis and trading-pattern evaluation.

---

## 🎓 Background

Developed as part of the **MSc Cloud Computing programme at the University of Surrey**, this project explored how cloud services can be combined to build and evaluate a distributed financial risk analysis application.

The project focused on combining application hosting, serverless computing, virtual-machine-based computation and cloud storage while considering **performance, resource management, execution time and cloud cost**.

---

## 👤 Author

### **Kishore Krishna Srinivasan**

**AI Product Engineer | Software Engineering, Data & Applied AI**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Kishore%20Krishna%20Srinivasan-blue?style=flat&logo=linkedin)](YOUR_LINKEDIN_URL)

---

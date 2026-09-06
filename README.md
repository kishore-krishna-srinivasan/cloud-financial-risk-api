# Cloud Financial Risk Analysis API

A cloud-based financial risk analysis application combining **Google App Engine, AWS Lambda, Amazon EC2 and Amazon S3** to analyse historical market data, evaluate trading signals and estimate financial risk using Monte Carlo simulation.

> MSc Cloud Computing Project - University of Surrey

## Overview

This project implements a Flask-based REST API that analyses historical Amazon (AMZN) market data and evaluates trading signals using statistical simulation.

The application supports two cloud-based compute approaches - **AWS Lambda and Amazon EC2**-  allowing analysis workloads to be executed using different compute models. Results and audit information are stored in Amazon S3, while the application provides endpoints for resource initialisation, readiness checks, analysis, cost estimation, result retrieval and resource termination.

The project demonstrates the design and implementation of a **multi-cloud application architecture** combining managed application hosting, serverless computing, virtual-machine-based computation and cloud storage.

## Architecture

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
      │ Serverless   │           │ Cloud Compute│
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
##Architecture Components

| Component               | Purpose                                                                    |
| ----------------------- | -------------------------------------------------------------------------- |
| **Google App Engine**   | Hosts the Flask REST API                                                   |
| **AWS Lambda**          | Provides serverless execution for analysis and cloud-management operations |
| **Amazon EC2**          | Provides VM-based compute for analysis workloads                           |
| **Amazon S3**           | Stores analysis results, audit information and generated charts            |
| **AWS Systems Manager** | Supports remote execution and management of EC2 analysis workloads         |
| **AWS Cost Explorer**   | Provides cloud-cost information for resource usage analysis                |

Request Flow

The application follows a cloud-based workflow for executing and retrieving financial analysis:

Client
  │
  ▼
Flask REST API
  │
  ├── Initialise compute resources
  │
  ├── AWS Lambda
  │      │
  │      └── Financial analysis
  │
  └── Amazon EC2
         │
         └── Financial analysis
                 │
                 ▼
             Amazon S3
                 │
                 ├── Results
                 ├── Audit information
                 └── Generated charts
                 │
                 ▼
             Flask API
                 │
                 ▼
               Client

Workflow
The client sends an analysis or resource-management request to the Flask API.
The application initialises either AWS Lambda or EC2 compute resources.
Historical market data is retrieved and processed.
Trading signals are generated from the market data.
Monte Carlo simulations are executed using the selected compute service.
Risk and profit/loss results are generated.
Results and audit information are stored in Amazon S3.
The API provides endpoints for retrieving analysis results, charts, execution information and audit data.
Cloud resources can be monitored and terminated when they are no longer required.

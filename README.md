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

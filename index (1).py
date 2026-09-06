# The main Flask application script for running API Endpoints

# Standard library imports
import os
import json
import time
import io
import random
import tempfile
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Flask web framework imports
from flask import Flask, request, jsonify, send_file

# Data handling imports
import pandas as pd
import numpy as np

# Plotting and visualization imports
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# AWS SDK and local environment configuration
import boto3
from dotenv import load_dotenv

# Financial data imports
import yfinance as yf

# Load local environment variables when running the application locally.
# AWS credentials are intentionally NOT stored in this repository.
load_dotenv()

#Starting the Flask application
app = Flask(__name__)

# Initializing the configuration to store instance IDs, service types, time frames and termination status
app.config['EC2_INSTANCE_IDS'] = []
app.config['LAST_SERVICE'] = None
app.config['LAST_REPLICAS'] = 0
app.config['WARMUP_START_TIME'] = None
app.config['WARMUP_END_TIME'] = None
app.config['SERVICE_TERMINATED'] = False

# 1. Defining Warmup Endpoint
@app.route('/warmup', methods=['POST'])
def warmup():
    # Extracting the JSON payload from the POST request
    data = request.get_json()
    
    # Extracting the service type ('s') and the number of replicas ('r') from the request data
    service = data.get('s')
    replicas = int(data.get('r', 1))

    # Marking the start time of the warmup process
    app.config['WARMUP_START_TIME'] = time.time()

    # Determining which service to initialize based on the service type
    if service == 'lambda':
        app.config['LAST_SERVICE'] = 'lambda'
        app.config['LAST_REPLICAS'] = replicas
        return warmup_lambda_functions(replicas)
    elif service == 'ec2':
        app.config['LAST_SERVICE'] = 'ec2'
        app.config['LAST_REPLICAS'] = replicas
        return warmup_ec2_instances(replicas)
    else:
        # Returning an error response if the service type is unsupported
        return jsonify({'error': 'Unsupported service type provided'}), 400

def warmup_lambda_functions(replicas):
    try:
        # Initializing the AWS Lambda client with credentials from environment variables
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # List to store results of each Lambda function invocation
        results = []
        function_name = 'warmup_lsa'  # The name of the Lambda function to invoke

        # Invoking the Lambda function the specified number of times (replicas)
        for _ in range(replicas):
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse'
            )
            # Reading and decoding the response payload
            payload = response['Payload'].read().decode('utf-8')
            result = json.loads(payload)
            results.append(result)
        
        # Marking the end time of the warmup process
        app.config['WARMUP_END_TIME'] = time.time()
        app.config['SERVICE_TERMINATED'] = False

        # Returning a JSON response with the results of the Lambda function invocations
        return jsonify({'result': 'ok', 'message': 'Lambda functions invoked', 'details': results}), 200
    except Exception as e:
        # Handling any exceptions that occur during the invocation process
        return jsonify({'error': str(e)}), 500

def warmup_ec2_instances(replicas):
    try:
        # Initializing the AWS EC2 client with credentials from environment variables
        ec2_client = boto3.client('ec2', region_name='us-east-1')

        # Launching EC2 instances with the specified parameters
        instances = ec2_client.run_instances(
            ImageId='ami-0fe75f2c973fdfa1c',  # AMI ID
            InstanceType='t2.micro',  # Instance type
            MinCount=replicas,  # Minimum number of instances to launch
            MaxCount=replicas,  # Maximum number of instances to launch
            KeyName='clouldcwkey'  # EC2 Key pair
        )

        # Extracting the instance IDs from the response
        instance_ids = [instance['InstanceId'] for instance in instances['Instances']]
        
        # Storing instance IDs in the app configuration for readiness check
        app.config['EC2_INSTANCE_IDS'] = instance_ids
        
        # Marking the end time of the warmup process
        app.config['WARMUP_END_TIME'] = time.time()
        app.config['SERVICE_TERMINATED'] = False

        # Returning a JSON response with the instance IDs of the launched EC2 instances
        return jsonify({'result': 'ok', 'message': 'EC2 instances initialized', 'instance_ids': instance_ids}), 200
    except Exception as e:
        # Handling any exceptions that occur during the instance launch process
        return jsonify({'error': str(e)}), 500

# 2. Defining Scaled Ready Endpoint
@app.route('/scaled_ready', methods=['GET'])
def scaled_ready():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    last_service = app.config.get('LAST_SERVICE')
    if not last_service:
        return jsonify({'error': 'No service has been warmed up yet'}), 400

    if last_service == 'lambda':
        # For Lambda, readiness occurs upon invocation
        return jsonify({'warm': True}), 200
    elif last_service == 'ec2':
        return check_ec2_instances_ready()
    else:
        return jsonify({'error': 'Unsupported service type'}), 400

def check_ec2_instances_ready():
    try:
        # Initializing the AWS EC2 client with credentials from environment variables
        ec2_client = boto3.client('ec2', region_name='us-east-1')

        # Retrieving instance IDs from the application configuration
        instance_ids = app.config.get('EC2_INSTANCE_IDS', [])
        
        if not instance_ids:
            print("No instances to check.")
            return jsonify({'warm': False}), 200
        
        # Describing the status of the instances
        response = ec2_client.describe_instance_status(InstanceIds=instance_ids, IncludeAllInstances=True)
        instance_statuses = response.get('InstanceStatuses', [])
        
        all_ready = True
        # Checking the status of each instance
        for status in instance_statuses:
            instance_id = status['InstanceId']
            instance_state = status['InstanceState']['Name']
            instance_status = status.get('InstanceStatus', {}).get('Status', 'Unknown')
            system_status = status.get('SystemStatus', {}).get('Status', 'Unknown')
            print(f"Instance ID: {instance_id}, State: {instance_state}, Instance Status: {instance_status}, System Status: {system_status}")
            
            if instance_state == 'running' and instance_status == 'ok' and system_status == 'ok':
                print(f"Instance {instance_id} is ready.")
            else:
                all_ready = False
                print(f"Instance {instance_id} is not ready. State: {instance_state}, Instance Status: {instance_status}, System Status: {system_status}")
        
        # Returning the readiness status
        print(f"All instances ready: {all_ready}")
        return jsonify({'warm': all_ready}), 200
    except Exception as e:
        # Handling any exceptions that occur during the status check process
        return jsonify({'error': str(e)}), 500

# 3. Defining Get Warmup Cost Endpoint
@app.route('/get_warmup_cost', methods=['GET'])
def get_warmup_cost():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    last_service = app.config.get('LAST_SERVICE')
    replicas = app.config.get('LAST_REPLICAS', 1)
    start_time = app.config.get('WARMUP_START_TIME')
    end_time = app.config.get('WARMUP_END_TIME')

    if not last_service or not start_time or not end_time:
        return jsonify({'error': 'No service has been warmed up yet'}), 400

    # Calculating the total billable time in seconds
    billable_time = end_time - start_time

    if last_service == 'lambda':
        cost = calculate_lambda_cost(replicas, billable_time)
    elif last_service == 'ec2':
        cost = calculate_ec2_cost(replicas, billable_time)
    else:
        return jsonify({'error': 'Unsupported service type provided'}), 400

    return jsonify({'billable_time': billable_time, 'cost': cost}), 200

def calculate_lambda_cost(replicas, billable_time):
    # Lambda cost calculation
    cost_per_million_requests = 0.20
    cost_per_ms = 0.00001667 / 1000  # $0.00001667 per GB-second, taking 1ms and 128MB memory
    duration_ms = billable_time * 1000  # Converting seconds to milliseconds

    # Calculating the cost per request
    cost_per_request = cost_per_million_requests / 1_000_000 + cost_per_ms * duration_ms
    total_cost = cost_per_request * replicas

    return total_cost

def calculate_ec2_cost(replicas, billable_time):
    # EC2 cost calculation
    cost_per_hour = 0.0116   #AWS pricing for EC2 per hour
    warmup_duration_hours = billable_time / 3600  # Duration of the warmup

    # Calculate the total cost for instances
    total_cost = cost_per_hour * warmup_duration_hours * replicas

    return total_cost
    
# 4. Defining Analyse Endpoint

# Global variable to store the results
results = {
    "var95": [],
    "var99": [],
    "profit_loss": [],
    "total_profit_loss": 0.0,
    "chart_file_path": None,
    "time_cost": {"time": 0.0, "cost": 0.0},
    "audit_data": []
}

# Global variable to track the termination status
is_terminated = False

# Function to save audit data to S3
def save_audit_data(service, replicas, h, d, t, p, total_profit_loss, avg_var95, avg_var99, analysis_time, analysis_cost):
    s3 = boto3.client('s3', region_name='us-east-1')
    
    bucket_name = 'analysebucks3'
    audit_key = 'audit/audit_data.json'
    
    # Defining Audit entries
    audit_entry = {
        "service": service,
        "replicas": replicas,
        "h": h,
        "d": d,
        "t": t,
        "p": p,
        "total_profit_loss": total_profit_loss,
        "avg_var95": avg_var95,
        "avg_var99": avg_var99,
        "time": analysis_time,
        "cost": analysis_cost
    }
    
    # Loading the existing audit data if available
    try:
        existing_audit_data = s3.get_object(Bucket=bucket_name, Key=audit_key)
        audit_data = json.loads(existing_audit_data['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        audit_data = []
    
    # Appending the new audit entry
    audit_data.append(audit_entry)
    
    # Saving the updated audit data back to S3
    s3.put_object(Bucket=bucket_name, Key=audit_key, Body=json.dumps(audit_data))
    
    return True

# Function to get audit data from S3
def get_audit_data():
    s3 = boto3.client('s3', region_name='us-east-1')
    
    bucket_name = 'analysebucks3'
    audit_key = 'audit/audit_data.json'
    
    try:
        existing_audit_data = s3.get_object(Bucket=bucket_name, Key=audit_key)
        audit_data = json.loads(existing_audit_data['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        audit_data = []
    
    return audit_data

# Function to fetch stock data from Yahoo Finance
def fetch_stock_data(ticker, start, end):
    # Downloading Amazon Stock data
    data = yf.download(ticker, start=start, end=end)
    if data.empty:
        raise ValueError("No data returned from Yahoo Finance.")
    
    # Ensuring all necessary columns are present, even if they are empty
    data['Dividends'] = data.get('Dividends', pd.Series([0] * len(data)))
    data['Stock Splits'] = data.get('Stock Splits', pd.Series([0] * len(data)))
    data['Date'] = data.index
    data.reset_index(drop=True, inplace=True)
    return data

# Function to analyze stock data and generate trading signals based on price changes
def analyze_signals(data, threshold=0.01):
    # Initializing signals with default
    data['Buy'] = 0
    data['Sell'] = 0

    # Analyzing stock price movements to generate buy or sell signals using Three White Soldiers and Black Crows
    for i in range(2, len(data)):
        body_size = data['Close'][i] - data['Open'][i]
        if (body_size >= threshold * data['Close'][i] and
            (data['Close'][i-1] - data['Open'][i-1]) >= threshold * data['Close'][i-1] and
            (data['Close'][i-2] - data['Open'][i-2]) >= threshold * data['Close'][i-2]):
            data.at[i, 'Buy'] = 1
        elif (body_size <= -threshold * data['Close'][i] and
              (data['Open'][i-1] - data['Close'][i-1]) >= threshold * data['Close'][i-1] and
              (data['Open'][i-2] - data['Close'][i-2]) >= threshold * data['Close'][i-2]):
            data.at[i, 'Sell'] = 1
    return data

# Function to prepare stock data for storage or further processing
def prepare_data_for_storage(data):
    # Standardizing the 'Date' format and selecting relevant data for storage
   data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
   return data[['Date', 'Close', 'Buy', 'Sell']].to_dict('records')
    
# Function to invoke EC2 Analysis
def invoke_ec2_analysis(data, h, d, t, p):
    start_time = time.time()

    try:
        # Initializing the S3 client
        s3_client = boto3.client('s3', region_name='us-east-1')
        ssm_client = boto3.client('ssm', region_name='us-east-1')

        # Defining bucket and file names
        bucket_name = 'analysebucks3'
        input_data_key = 'analysis/input_data.json'
        output_data_key = 'analysis/output_data.json'

        # Converting the DataFrame to JSON string and uploading to S3
        input_data = {
            "data": data.to_dict(),
            "h": h,
            "d": d,
            "t": t,
            "p": p
        }
        s3_client.put_object(Bucket=bucket_name, Key=input_data_key, Body=json.dumps(input_data))

        # Sending SSM command to EC2 instances
        instance_ids = app.config.get('EC2_INSTANCE_IDS', [])
        if not instance_ids:
            return jsonify({"error": "No EC2 instances available"}), 400

        commands = [
            f'aws s3 cp s3://{bucket_name}/{input_data_key} /tmp/input_data.json',
            f'python3 /path/to/run_analysis.py /tmp/input_data.json /tmp/output_data.json',
            f'aws s3 cp /tmp/output_data.json s3://{bucket_name}/{output_data_key}'
        ]
        response = ssm_client.send_command(
            InstanceIds=instance_ids,
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': commands}
        )

        command_id = response['Command']['CommandId']
        time.sleep(10)  # Initial wait time for command execution

        # Retrieving the command execution result
        result = ssm_client.list_command_invocations(
            CommandId=command_id,
            InstanceId=instance_ids[0],
            Details=True
        )

        # Waiting until the command execution is finished and fetching the result from S3
        ssm_client.get_waiter('command_executed').wait(CommandId=command_id, InstanceIds=instance_ids)
        output = s3_client.get_object(Bucket=bucket_name, Key=output_data_key)
        analysis_result = json.loads(output['Body'].read().decode('utf-8'))

        end_time = time.time()
        analysis_time = end_time - start_time
        cost_per_second = 0.0000115  # Instance cost per hour is 0.0416, so the cost for a second is 0.0416/3600
        analysis_cost = analysis_time * cost_per_second

        results.update({
            "var95": analysis_result.get("var95", []),
            "var99": analysis_result.get("var99", []),
            "profit_loss": analysis_result.get("profit_loss", []),
            "total_profit_loss": analysis_result.get("total_profit_loss", 0.0),
            "time_cost": {"time": analysis_time, "cost": analysis_cost}
        })

        return jsonify({"result": "ok", "service": "ec2"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to invoke Lambda for analysis
def invoke_lambda_analysis(data, h, d, t, p):
    global results
    try:
        # Initializing the AWS Lambda client with credentials from environment variables
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Lambda function name for analysis
        function_name = 'analyse_api'

        # Payload to send to the Lambda function
        payload = {
            'data': data,
            'h': h,
            'd': d,
            't': t,
            'p': p
        }

        replicas = app.config.get('LAST_REPLICAS', 1)
        start_time = time.time()

        # Function to invoke the Lambda function
        def invoke():
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            return json.loads(response['Payload'].read().decode('utf-8'))

        # Using ThreadPoolExecutor to run multiple invocations concurrently
        with ThreadPoolExecutor(max_workers=replicas) as executor:
            futures = [executor.submit(invoke) for _ in range(replicas)]
            combined_results = {
                'var95': [],
                'var99': [],
                'profit_loss': [],
                'total_profit_loss': 0.0
            }
            for future in as_completed(futures):
                result = future.result()
                body = json.loads(result['body'])
                combined_results['var95'].extend([res['var95'] for res in body['results']])
                combined_results['var99'].extend([res['var99'] for res in body['results']])
                combined_results['profit_loss'].extend([res['profit_loss'] for res in body['results']])
                combined_results['total_profit_loss'] += body['total_profit_loss']
        
        end_time = time.time()
        
        # Calculating and storing time and cost
        analysis_time = end_time - start_time
        cost_per_second = 0.00001667  # Example cost per second of analysis
        analysis_cost = analysis_time * cost_per_second

        results.update({
            "var95": combined_results['var95'],
            "var99": combined_results['var99'],
            "profit_loss": combined_results['profit_loss'],
            "total_profit_loss": combined_results['total_profit_loss'],
            "time_cost": {"time": analysis_time, "cost": analysis_cost}
        })

        return jsonify({"result": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        # Termination status check
        if app.config.get('SERVICE_TERMINATED'):
            return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
    try:
        # Extracting the JSON payload from the POST request
        data_input = request.get_json()
        print("Received in Flask:", json.dumps(data_input))

        # Extracting and verifying all required parameters are present
        required_params = ['h', 'd', 't', 'p']
        missing_params = [param for param in required_params if param not in data_input]
        if missing_params:
            return jsonify({'error': f"Missing required parameters: {','.join(missing_params)}"}), 400

        # Extracting input parameters
        h = int(data_input['h'])
        d = int(data_input['d'])
        t = data_input['t'].lower()
        p = int(data_input['p'])

        # Preparing the stock data
        today = datetime.today()
        past_time = today - timedelta(days=50*365)
        data = fetch_stock_data('AMZN', past_time, today)  # Fetching Amazon stock data
        data = analyze_signals(data)  # Analyzing buy/sell signals

        # Preparing the simplified data for analysis
        simplified_data = prepare_data_for_storage(data)
        # Retreiving last used service and relicas
        last_service = app.config.get('LAST_SERVICE')
        replicas = app.config.get('LAST_REPLICAS', 1)

        # Calling appropriate service analysis function
        if last_service == 'lambda':
            response = invoke_lambda_analysis(simplified_data, h, d, t, p)
        elif last_service == 'ec2':
            response = invoke_ec2_analysis(data, h, d, t, p)
        else:
            return jsonify({"error": "No valid service type configured"}), 400

        # Calculating and saving audit data for respective services
        if last_service == 'lambda':
            avg_var95 = np.mean(results["var95"]) if results["var95"] else 0
            avg_var99 = np.mean(results["var99"]) if results["var99"] else 0
            save_audit_data('lambda', replicas, h, d, t, p, results['total_profit_loss'], avg_var95, avg_var99, results['time_cost']['time'], results['time_cost']['cost'])

        elif last_service == 'ec2':
            avg_var95 = np.mean(results["var95"]) if results["var95"] else 0
            avg_var99 = np.mean(results["var99"]) if results["var99"] else 0
            save_audit_data('ec2', replicas, h, d, t, p, results['total_profit_loss'], avg_var95, avg_var99, results['time_cost']['time'], results['time_cost']['cost'])
        else:
            return jsonify({"error": "No valid service type configured"}), 400
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# 5. Defining Signal VaR 95% and 99% Endpoint
@app.route('/get_sig_vars9599', methods=['GET'])
def get_sig_vars9599():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    global results
    return jsonify({
        "var95": results.get("var95", []),
        "var99": results.get("var99", [])
    })

# 6. Defining Average VaR 95% and 99% Endpoint
@app.route('/get_avg_vars9599', methods=['GET'])
def get_avg_vars9599():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    global results
    avg_var95 = np.mean(results["var95"]) if results["var95"] else 0
    avg_var99 = np.mean(results["var99"]) if results["var99"] else 0
    return jsonify({"avg_var95": avg_var95, "avg_var99": avg_var99})

# 7. Defining Signal Profit/Loss Endpoint
@app.route('/get_sig_profit_loss', methods=['GET'])
def get_sig_profit_loss():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    global results
    return jsonify({"profit_loss": results.get("profit_loss", [])})

# 8. Defining Total Profit/Loss Endpoint
@app.route('/get_tot_profit_loss', methods=['GET'])
def get_tot_profit_loss():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    global results
    return jsonify({"total_profit_loss": results.get("total_profit_loss", 0.0)})
    
# 9. Defining Chart URL Endpoint
# Function to generate a chart and save it to an S3 bucket

def generate_and_upload_chart(results):
    var95 = results['var95']
    var99 = results['var99']
    
    avg_var95 = np.mean(var95)
    avg_var99 = np.mean(var99)
    
    fig, ax = plt.subplots()
    ax.plot(var95, label='VaR 95%')
    ax.plot(var99, label='VaR 99%')
    ax.axhline(y=avg_var95, color='r', linestyle='--', label='Average VaR 95%')
    ax.axhline(y=avg_var99, color='b', linestyle='--', label='Average VaR 99%')
    ax.legend()
    
    ax.set_title('Monte Carlo Simulations - Values at Risk Analysis')
    ax.set_xlabel('Index')
    ax.set_ylabel('Values at Risk')
    
    # Saving the chart to a file
    chart_path = '/tmp/chart.png'
    plt.savefig(chart_path)
    plt.close(fig)
    
    # Uploading the chart to S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    
    bucket_name = 'analysebucks3'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    s3_key = f"charts/chart-{timestamp}.png"
    
    s3.upload_file(chart_path, bucket_name, s3_key)
    
    # Defining the structure of the URL
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    
    return s3_url
    
@app.route('/get_chart_url', methods=['GET'])
def get_chart_url():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    try:
        if not results['var95'] and not results['var99']:
            return jsonify({"error": "No chart available. Please run the analysis first."}), 400
        # Generating and uploading the chart
        s3_url = generate_and_upload_chart(results)
        
        return jsonify({"url": s3_url}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 10. Defining Time and Cost Endpoint
@app.route('/get_time_cost', methods=['GET'])
def get_time_cost():
    if app.config.get('SERVICE_TERMINATED'):
        return jsonify({'error': 'Service has been terminated. Please warm up again to proceed.'}), 400
    global results
    time_cost = results.get('time_cost', {"time": 0.0, "cost": 0.0})
    return jsonify(time_cost), 200
    
# 11. Defining Audit Endpoint
@app.route('/get_audit', methods=['GET'])
def get_audit():
    try:
    # Calling the Function to get audit data from S3
        audit_data = get_audit_data()
        return jsonify(audit_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
# 12. Defining Reset Endpoint
@app.route('/reset', methods=['GET'])
def reset():
    global results
    # Clearing the results dictionary
    results = {
        "var95": [],
        "var99": [],
        "profit_loss": [],
        "total_profit_loss": 0.0,
        "chart_file_path": None,
        "time_cost": {"time": 0.0, "cost": 0.0}
    }
    return jsonify({"result": "ok"}), 200
    
# 13. Defining Terminate Endpoint

# Function to perform the termination of instances
def terminate_ec2_instances():
    try:
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        
        instance_ids = app.config.get('EC2_INSTANCE_IDS', [])
        if not instance_ids:
            return

        # Terminating the EC2 instances
        ec2_client.terminate_instances(InstanceIds=instance_ids)

        # Waiting for the termination to complete
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)

        # Clearing the instance IDs from the configuration
        app.config['EC2_INSTANCE_IDS'] = []
    except Exception as e:
        print(f"Error terminating EC2 instances: {str(e)}")

# Function to check the status of termination
def check_ec2_termination_status():
    try:
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        
        # Retreiving the Instance IDS
        instance_ids = app.config.get('EC2_INSTANCE_IDS', [])
        if not instance_ids:
            return jsonify({'terminated': True}), 200

        # Requesting to describe the instances to check the current state
        response = ec2_client.describe_instances(InstanceIds=instance_ids)
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] not in ['terminated', 'shutting-down']:
                    return jsonify({'terminated': False}), 200

        return jsonify({'terminated': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/terminate', methods=['GET'])
def terminate():
    try:
        # Terminating the EC2 instances if the last service was EC2
        if app.config.get('LAST_SERVICE') == 'ec2':
            terminate_ec2_instances()
        app.config['SERVICE_TERMINATED'] = True
            
        # Setting the SERVICE_TERMINATED flag to True for Lambda
        if app.config.get('LAST_SERVICE') == 'lambda':
            app.config['SERVICE_TERMINATED'] = True
        
        return jsonify({'result': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 14. Defining Scaled Terminated Endpoint
@app.route('/scaled_terminated', methods=['GET'])
def scaled_terminated():
    # Checking for the termination status of appropriate scalable service
    if app.config.get('LAST_SERVICE') == 'ec2':
        return check_ec2_termination_status()
    elif app.config.get('LAST_SERVICE') == 'lambda':
        return jsonify({'terminated': app.config.get('SERVICE_TERMINATED', False)}), 200
    else:
        return jsonify({'error': 'No valid service type configured'}), 400
        
# 15. Defining Get Endpoints to retrieve call strings
@app.route('/get_endpoints', methods=['GET'])
def get_endpoints():
    base_url = request.host_url.rstrip('/')
    
    # Retrieving the last used values or default values
    last_service = app.config.get('LAST_SERVICE', 'lambda')
    last_replicas = app.config.get('LAST_REPLICAS', 1)
    last_h = app.config.get('LAST_H', 101)
    last_d = app.config.get('LAST_D', 10000)
    last_t = app.config.get('LAST_T', 'buy')
    last_p = app.config.get('LAST_P', 7)
    
    endpoints = [
        {"endpoint": f"{base_url}/warmup", "callstring": f"curl -X POST {base_url}/warmup -H \"Content-Type: application/json\" -d '{{\"s\": \"{last_service}\", \"r\": {last_replicas}}}'"},
        {"endpoint": f"{base_url}/scaled_ready", "callstring": f"curl -X GET {base_url}/scaled_ready"},
        {"endpoint": f"{base_url}/get_warmup_cost", "callstring": f"curl -X GET {base_url}/get_warmup_cost"},
        {"endpoint": f"{base_url}/analyse", "callstring": f"curl -X POST {base_url}/analyse -H \"Content-Type: application/json\" -d '{{\"h\": {last_h}, \"d\": {last_d}, \"t\": \"{last_t}\", \"p\": {last_p}}}'"},
        {"endpoint": f"{base_url}/get_sig_vars9599", "callstring": f"curl -X GET {base_url}/get_sig_vars9599"},
        {"endpoint": f"{base_url}/get_avg_vars9599", "callstring": f"curl -X GET {base_url}/get_avg_vars9599"},
        {"endpoint": f"{base_url}/get_sig_profit_loss", "callstring": f"curl -X GET {base_url}/get_sig_profit_loss"},
        {"endpoint": f"{base_url}/get_tot_profit_loss", "callstring": f"curl -X GET {base_url}/get_tot_profit_loss"},
        {"endpoint": f"{base_url}/get_chart_url", "callstring": f"curl -X GET {base_url}/get_chart_url"},
        {"endpoint": f"{base_url}/get_time_cost", "callstring": f"curl -X GET {base_url}/get_time_cost"},
        {"endpoint": f"{base_url}/get_audit", "callstring": f"curl -X GET {base_url}/get_audit"},
        {"endpoint": f"{base_url}/reset", "callstring": f"curl -X GET {base_url}/reset"},
        {"endpoint": f"{base_url}/terminate", "callstring": f"curl -X GET {base_url}/terminate"},
        {"endpoint": f"{base_url}/scaled_terminated", "callstring": f"curl -X GET {base_url}/scaled_terminated"}
    ]
    
    return jsonify(endpoints), 200

if __name__ == "__main__":
    # Starting the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)

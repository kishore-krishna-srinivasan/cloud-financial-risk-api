import json
import random
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError

def lambda_handler(event, context):
    # Initialize Amazon S3 resource interface
    s3_resource = boto3.resource('s3')
    analysis_bucket = 'analysebucks3'

    # Deserialize and normalize input data
    try:
        event_data = json.loads(event['body']) if 'body' in event else event
        analysis_params = parse_analysis_parameters(event_data)
        analysis_results = perform_analysis(analysis_params)
        results_path = store_results(s3_resource, analysis_bucket, analysis_results, analysis_params)
        log_audit(s3_resource, analysis_bucket, analysis_results, analysis_params)
        return construct_response(200, 'ok', results_path)
    except json.JSONDecodeError as e:
        return construct_response(400, f"Invalid JSON in request: {str(e)}")
    except ValueError as e:
        return construct_response(400, f"Parameter validation error: {str(e)}")
    except ClientError as e:
        return construct_response(500, f"AWS service error: {str(e)}")
    except Exception as e:
        return construct_response(500, f"Internal server error: {str(e)}")

def parse_analysis_parameters(data):
    if not all(k in data for k in ['data', 'h', 'd', 't', 'p']):
        missing_keys = ', '.join(k for k in ['data', 'h', 'd', 't', 'p'] if k not in data)
        raise ValueError(f"Missing required parameters: {missing_keys}")
    return {
        'data': data['data'],
        'h': int(data['h']),
        'd': int(data['d']),
        't': data['t'].capitalize(),
        'p': int(data['p'])
    }

def perform_analysis(params):
    # Dummy implementation for demonstration purposes
    results = [{'var95': random.uniform(-0.05, 0.05), 'var99': random.uniform(-0.1, 0.1), 'profit_loss': random.uniform(-0.1, 0.1)} for _ in range(10)]
    return {
        'results': results,
        'average_var95': sum(item['var95'] for item in results) / len(results),
        'average_var99': sum(item['var99'] for item in results) / len(results),
        'total_profit_loss': sum(item['profit_loss'] for item in results)
    }

def store_results(s3, bucket_name, results, params):
    file_path = f"results/results_{params['t']}.json" 
    s3.Object(bucket_name, file_path).put(Body=json.dumps(results['results']))
    return file_path

def log_audit(s3, bucket_name, results, params):
    audit_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'parameters': params,
        'results': results
    }
    s3.Object(bucket_name, 'audit/audit_log.json').put(Body=json.dumps(audit_data))

def construct_response(status_code, result, data_path=None):
    body = {'result': result}
    if data_path:
        body['results_path'] = data_path
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }


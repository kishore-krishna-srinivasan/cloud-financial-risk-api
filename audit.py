import json
import boto3

def lambda_handler(event, context):
    event = json.loads(event['body']) if 'body' in event else event
    
    #Retreiving bucket name
    bucket_name = event.get('bucket_name')
    #Fetching audit key
    audit_res_key = event.get('audit_res_key')
    
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=audit_res_key)
        audit_log_content = response['Body'].read().decode('utf-8')
        return {
            'statusCode': 200,
            'body': audit_log_content
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


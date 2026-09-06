import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging

def handle_instance_creation(event_payload, lambda_context):
    ec2_service = boto3.resource('ec2', region_name='us-east-1')

    try:
        if isinstance(event_payload, dict) and 'body' in event_payload:
            request_parameters = json.loads(event_payload['body'])
        else:
            request_parameters = event_payload
        
        ec2_type = request_parameters.get('ec2_type', 't2.micro')
        ami_id = request_parameters.get('ami_id', 'ami-0fe75f2c973fdfa1c')
        instance_quantity = int(request_parameters.get('instance_quantity', 1))

        deployment = ec2_service.create_instances(
            ImageId=ami_id,
            InstanceType=ec2_type,
            MinCount=instance_quantity,
            MaxCount=instance_quantity,
            KeyName='clouldcwkey',
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Coursework', 'Value': 'WarmupFunc'}]
            }]
        )
        ids = [machine.id for machine in deployment]
        return generate_response(200, f"Successfully launched EC2 instances: {ids}")
    except (BotoCoreError, ClientError, ValueError) as e:
        logging.error(f"Failed to launch instances: {e}")
        return generate_response(500, f"Error launching instances: {str(e)}")

def generate_response(status_code, message):
    return {'statusCode': status_code, 'body': json.dumps({'message': message})}

def lambda_handler(event, context):
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Received event: {event}")
    return handle_instance_creation(event, context)

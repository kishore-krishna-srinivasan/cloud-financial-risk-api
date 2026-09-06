import json
import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='us-east-1')
    tag_key = event.get('tag_key', 'Coursework')
    tag_value = event.get('tag_value', 'WarmupFunc')

    try:
        logging.info("Fetching instances with tag: %s=%s", tag_key, tag_value)
        instances = fetch_instances(ec2, tag_key, tag_value)
        is_warm = any(instance['State']['Name'] == 'running' for instance in instances)
        logging.info("Is system warm: %s", is_warm)
        return {
            'statusCode': 200,
            'body': json.dumps({'warm': is_warm})
        }
    except ClientError as error:
        logging.error("ClientError: %s", error)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to fetch instances', 'details': str(error)})
        }
    except Exception as error:
        logging.error("Unexpected error: %s", error)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'An internal error occurred', 'details': str(error)})
        }

def fetch_instances(ec2_client, tag_key, tag_value):
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    return [
        instance
        for reservation in response['Reservations']
        for instance in reservation['Instances']
    ]


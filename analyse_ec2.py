import json
import boto3
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event, context):
    # Log the received event
    logger.info(f"Received event: {json.dumps(event)}")

    # Extract values from the event
    data = event.get('data')
    minhistory = event.get('minhistory')
    shots = event.get('shots')
    transaction_type = event.get('t')
    check_days = event.get('p')

    # Log the extracted values
    logger.info(f"Processing with minhistory={minhistory}, shots={shots}, type={transaction_type}, check_days={check_days}")

    # Formulate the payload to be sent to EC2 instances
    payload = {
        'data': data,
        'minhistory': minhistory,
        'shots': shots,
        't': transaction_type,
        'p': check_days
    }

    # Initialize the EC2 client
    ec2 = boto3.client('ec2', region_name='us-east-1')
    tag_key = 'Coursework'
    tag_value = 'WarmupFunc'

    # Retrieve running EC2 instances with the specified tags
    instances = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    responses = []
    # Send the payload to each running instance
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            public_ip = instance.get('PublicIpAddress')
            if public_ip:
                url = f"http://{public_ip}/analyse"
                headers = {'Content-Type': 'application/json'}
                logger.info(f"Sending request to {url} with payload {json.dumps(payload)}")

                try:
                    response = requests.post(url, json=payload, headers=headers)
                    response_data = response.json() if response.status_code == 200 else response.text
                    responses.append({
                        'instance_id': instance['InstanceId'],
                        'public_ip': public_ip,
                        'response': response_data,
                        'status_code': response.status_code
                    })
                    logger.info(f"Received response from {public_ip}: {response_data}")
                except requests.RequestException as e:
                    responses.append({
                        'instance_id': instance['InstanceId'],
                        'public_ip': public_ip,
                        'error': str(e),
                        'status_code': 'Request Exception'
                    })
                    logger.error(f"Error contacting {public_ip}: {str(e)}")

    # Aggregate and return responses from all instances
    logger.info(f"All responses: {responses}")
    return {
        'statusCode': 200,
        'body': json.dumps({'responses': responses})
    }

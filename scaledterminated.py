import json
import boto3

def lambda_handler(event, context):
    # Decoding the event body directly for use
    request_data = json.loads(event['body']) if 'body' in event else event
    
    # Retrieving tags and region for instance filter
    tag_key = request_data.get('tag_key', 'Coursework')
    tag_value = request_data.get('tag_value', 'WarmupFunc')
    aws_region = request_data.get('region', 'us-east-1')

    # Initializing EC2 client in the specified region
    ec2_client = boto3.client('ec2', region_name=aws_region)

    try:
        # Filtering instances based on tags and checking their states
        ec2_response = ec2_client.describe_instances(
            Filters=[
                {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                {'Name': 'instance-state-name', 'Values': ['terminated', 'shutting-down']}
            ]
        )
        
        # Parsing response to find any instances that are not terminated
        instance_statuses = [
            instance['State']['Name']
            for reservation in ec2_response['Reservations']
            for instance in reservation['Instances']
        ]

        # Check if all instances are in a terminated state
        all_terminated = all(status == 'terminated' for status in instance_statuses)

        # Return the result with a clear indication of whether all instances are terminated
        return {
            'statusCode': 200,
            'body': json.dumps({'terminated': all_terminated})
        }
        
    except Exception as error:
        # Returning a detailed error response in case of failure
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Failed to process termination check: {str(error)}"})
        }


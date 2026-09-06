import json
import boto3

def lambda_handler(event, context):
    tag_key = event.get('tag_key', 'Coursework')
    tag_value = event.get('tag_value', 'WarmupFunc')
    region = event.get('region', 'us-east-1')

    ec2 = boto3.client('ec2', region_name=region)

    try:
        filters = [
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
        instances_response = ec2.describe_instances(Filters=filters)
        instance_ids = [
            instance['InstanceId'] 
            for reservation in instances_response['Reservations'] 
            for instance in reservation['Instances']
        ]

        if not instance_ids:
            return {'statusCode': 404, 'body': json.dumps({'message': 'No instances found to terminate'})}

        terminate_response = ec2.terminate_instances(InstanceIds=instance_ids)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Instances terminating',
                'instance_ids': instance_ids,
                'termination_details': terminate_response
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


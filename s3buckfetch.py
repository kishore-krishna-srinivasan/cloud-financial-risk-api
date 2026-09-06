import json
import boto3

def lambda_handler(event, context):
    bucket_name = event.get('bucket_name', 'analysebucks3') 

    s3 = boto3.client('s3')
    
    try:
        # List objects with the correct prefix
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='results/')
        if 'Contents' not in response:
            return {'statusCode': 404, 'body': json.dumps("No files found.")}
        
        files = [file['Key'] for file in response['Contents'] if 'Buy' in file['Key']]
        if not files:
            return {'statusCode': 404, 'body': json.dumps("No 'Buy' results files available.")}
        
        # Fetching  the first matching file
        selected_file = files[0]

        # Fetch the data from the selected file
        file_content = s3.get_object(Bucket=bucket_name, Key=selected_file)
        result_data = json.loads(file_content['Body'].read().decode('utf-8'))
        return {'statusCode': 200, 'body': json.dumps(result_data)}
    except Exception as error:
        return {'statusCode': 500, 'body': json.dumps({'error': str(error)})}


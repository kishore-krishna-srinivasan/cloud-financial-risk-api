import json
import boto3

def lambda_handler(event, context):
    s3_resource = boto3.resource('s3')

    # Parse the event body if it exists (common in API Gateway triggers)
    event_data = json.loads(event['body']) if 'body' in event else event
    
    # Extract bucket name and prefixes from the event data
    bucket_name = event_data.get('bucket_name')
    content_directories = event_data.get('content_directories')
    
    # Select the S3 bucket using the provided bucket name
    bucket = s3_resource.Bucket(bucket_name)
    cleanup_response = {
        'deleted_keys': [],
        'errors': []
    }

    try:
        # Process each prefix to delete the associated objects
        for prefix in content_directories:
            objects_to_remove = bucket.objects.filter(Prefix=prefix)
            keys_to_delete = [{'Key': obj.key} for obj in objects_to_remove]
            
            if keys_to_delete:
                # Attempt to delete the gathered objects
                deletion_result = bucket.delete_objects(Delete={'Objects': keys_to_delete})
                cleanup_response['deleted_keys'].extend(keys_to_delete)
                
                # Collect errors if any occurred during the deletion process
                if 'Errors' in deletion_result:
                    cleanup_response['errors'].extend(deletion_result['Errors'])

        # Return a success response with details of the deletion
        return {
            'statusCode': 200,
            'body': json.dumps(cleanup_response)
        }

    except Exception as error:
        # Return an error response if exceptions occur
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(error)})
        }


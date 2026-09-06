import json
import boto3
import base64
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    request = json.loads(event['body']) if 'body' in event else event
    storage_bucket = request.get('bucket_name')
    object_key = request.get('file_key')
    encoded_image = request.get('image_data')

    if not encoded_image:
        return response_format(400, "No image data provided.")

    image_content = base64.b64decode(encoded_image)
    s3_client = boto3.client('s3')

    try:
        s3_client.put_object(Bucket=storage_bucket, Key=object_key, Body=image_content, ContentType='image/png')
        image_url = f"https://{storage_bucket}.s3.amazonaws.com/{object_key}"
        return response_format(200, "Image uploaded successfully.", {'url': image_url})
    except ClientError as error:
        error_code = error.response['Error']['Code']
        if error_code == 'AllAccessDisabled':
            return response_format(403, "Access to the bucket has been disabled.")
        else:
            return response_format(500, f"Failed to upload image: {error_code}")
    except Exception as error:
        return response_format(500, f"Unexpected error: {str(error)}")

def response_format(status_code, message, data=None):
    body = {'message': message}
    if data:
        body.update(data)
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }


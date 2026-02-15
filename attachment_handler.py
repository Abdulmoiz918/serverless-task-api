import json
import boto3
import base64
import uuid
import os
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BUCKET_NAME = os.environ.get('S3_BUCKET', 'tasks-attachments-bucket')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'TasksTable')

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Handle file uploads for task attachments
    Supports uploading files and generating presigned URLs for downloads
    """
    print(f"Event received: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        if http_method == 'POST' and '/tasks/' in path and '/attachments' in path:
            return upload_attachment(event)
        elif http_method == 'GET' and '/tasks/' in path and '/attachments' in path:
            return get_attachments(event)
        elif http_method == 'DELETE' and '/attachments/' in path:
            return delete_attachment(event)
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Route not found'})
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)})
        }

def upload_attachment(event):
    """Upload a file attachment for a task"""
    try:
        task_id = event['pathParameters']['taskId']
        
        # Verify task exists
        task_response = table.get_item(Key={'taskId': task_id})
        if 'Item' not in task_response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('fileName') or not body.get('fileContent'):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'fileName and fileContent are required'})
            }
        
        file_name = body['fileName']
        file_content = body['fileContent']
        content_type = body.get('contentType', 'application/octet-stream')
        
        # Decode base64 content
        try:
            file_data = base64.b64decode(file_content)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Invalid base64 encoded file content'})
            }
        
        # Generate unique file key
        file_id = str(uuid.uuid4())
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        s3_key = f"tasks/{task_id}/{file_id}.{file_extension}" if file_extension else f"tasks/{task_id}/{file_id}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type,
            Metadata={
                'taskId': task_id,
                'originalFileName': file_name,
                'uploadedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Update task with attachment info
        attachment = {
            'fileId': file_id,
            'fileName': file_name,
            's3Key': s3_key,
            'contentType': content_type,
            'uploadedAt': datetime.utcnow().isoformat()
        }
        
        # Add attachment to task's attachments list
        table.update_item(
            Key={'taskId': task_id},
            UpdateExpression='SET attachments = list_append(if_not_exists(attachments, :empty_list), :attachment)',
            ExpressionAttributeValues={
                ':attachment': [attachment],
                ':empty_list': []
            }
        )
        
        # Generate presigned URL for immediate download
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'attachment': attachment,
                'downloadUrl': download_url
            })
        }
    except Exception as e:
        print(f"Error uploading attachment: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to upload attachment', 'error': str(e)})
        }

def get_attachments(event):
    """Get all attachments for a task with presigned download URLs"""
    try:
        task_id = event['pathParameters']['taskId']
        
        # Get task with attachments
        response = table.get_item(Key={'taskId': task_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        task = response['Item']
        attachments = task.get('attachments', [])
        
        # Generate presigned URLs for each attachment
        for attachment in attachments:
            s3_key = attachment.get('s3Key')
            if s3_key:
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                    ExpiresIn=3600
                )
                attachment['downloadUrl'] = download_url
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'taskId': task_id,
                'attachments': attachments,
                'count': len(attachments)
            })
        }
    except Exception as e:
        print(f"Error getting attachments: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to retrieve attachments', 'error': str(e)})
        }

def delete_attachment(event):
    """Delete a specific attachment"""
    try:
        task_id = event['pathParameters']['taskId']
        file_id = event['pathParameters']['fileId']
        
        # Get task
        response = table.get_item(Key={'taskId': task_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        task = response['Item']
        attachments = task.get('attachments', [])
        
        # Find and remove the attachment
        attachment_to_delete = None
        updated_attachments = []
        
        for attachment in attachments:
            if attachment.get('fileId') == file_id:
                attachment_to_delete = attachment
            else:
                updated_attachments.append(attachment)
        
        if not attachment_to_delete:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Attachment not found'})
            }
        
        # Delete from S3
        s3_key = attachment_to_delete.get('s3Key')
        if s3_key:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
        
        # Update task
        table.update_item(
            Key={'taskId': task_id},
            UpdateExpression='SET attachments = :attachments',
            ExpressionAttributeValues={':attachments': updated_attachments}
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Attachment deleted successfully'})
        }
    except Exception as e:
        print(f"Error deleting attachment: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to delete attachment', 'error': str(e)})
        }

def get_cors_headers():
    """Return CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
    }

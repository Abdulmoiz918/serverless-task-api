import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'TasksTable')
BUCKET_NAME = os.environ.get('S3_BUCKET', 'tasks-attachments-bucket')

table = dynamodb.Table(TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Main handler for task management operations
    Routes requests based on HTTP method and path
    """
    print(f"Event received: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path')
    
    try:
        # Route to appropriate handler
        if http_method == 'POST' and path == '/tasks':
            return create_task(event)
        elif http_method == 'GET' and path == '/tasks':
            return get_all_tasks(event)
        elif http_method == 'GET' and '/tasks/' in path:
            return get_task(event)
        elif http_method == 'PUT' and '/tasks/' in path:
            return update_task(event)
        elif http_method == 'DELETE' and '/tasks/' in path:
            return delete_task(event)
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

def create_task(event):
    """Create a new task"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('title'):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Title is required'})
            }
        
        task_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        task = {
            'taskId': task_id,
            'title': body['title'],
            'description': body.get('description', ''),
            'status': body.get('status', 'pending'),
            'priority': body.get('priority', 'medium'),
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        # Add optional due date
        if body.get('dueDate'):
            task['dueDate'] = body['dueDate']
        
        # Save to DynamoDB
        table.put_item(Item=task)
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps(task, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error creating task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to create task', 'error': str(e)})
        }

def get_all_tasks(event):
    """Get all tasks with optional filtering"""
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        status_filter = query_params.get('status')
        
        if status_filter:
            # Filter by status
            response = table.scan(
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status_filter}
            )
        else:
            # Get all tasks
            response = table.scan()
        
        tasks = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'tasks': tasks,
                'count': len(tasks)
            }, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to retrieve tasks', 'error': str(e)})
        }

def get_task(event):
    """Get a specific task by ID"""
    try:
        task_id = event['pathParameters']['taskId']
        
        response = table.get_item(Key={'taskId': task_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response['Item'], cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error getting task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to retrieve task', 'error': str(e)})
        }

def update_task(event):
    """Update an existing task"""
    try:
        task_id = event['pathParameters']['taskId']
        body = json.loads(event.get('body', '{}'))
        
        # Check if task exists
        existing = table.get_item(Key={'taskId': task_id})
        if 'Item' not in existing:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        # Build update expression
        update_expr = "SET updatedAt = :updated"
        expr_values = {':updated': datetime.utcnow().isoformat()}
        expr_names = {}
        
        if 'title' in body:
            update_expr += ", title = :title"
            expr_values[':title'] = body['title']
        
        if 'description' in body:
            update_expr += ", description = :desc"
            expr_values[':desc'] = body['description']
        
        if 'status' in body:
            update_expr += ", #status = :status"
            expr_values[':status'] = body['status']
            expr_names['#status'] = 'status'
        
        if 'priority' in body:
            update_expr += ", priority = :priority"
            expr_values[':priority'] = body['priority']
        
        if 'dueDate' in body:
            update_expr += ", dueDate = :dueDate"
            expr_values[':dueDate'] = body['dueDate']
        
        # Update the task
        response = table.update_item(
            Key={'taskId': task_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names if expr_names else None,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response['Attributes'], cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error updating task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to update task', 'error': str(e)})
        }

def delete_task(event):
    """Delete a task"""
    try:
        task_id = event['pathParameters']['taskId']
        
        # Check if task exists
        existing = table.get_item(Key={'taskId': task_id})
        if 'Item' not in existing:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Task not found'})
            }
        
        # Delete the task
        table.delete_item(Key={'taskId': task_id})
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Task deleted successfully'})
        }
    except Exception as e:
        print(f"Error deleting task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'Failed to delete task', 'error': str(e)})
        }

def get_cors_headers():
    """Return CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

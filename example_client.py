#!/usr/bin/env python3
"""
Example Python client for the Serverless Task Management API
Demonstrates how to interact with the API programmatically
"""

import requests
import json
import base64
from typing import Dict, List, Optional

class TaskAPIClient:
    """Client for interacting with the Serverless Task API"""
    
    def __init__(self, api_endpoint: str):
        """
        Initialize the API client
        
        Args:
            api_endpoint: Base URL of the API (e.g., https://xxx.execute-api.us-east-1.amazonaws.com/dev)
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        
    def create_task(self, title: str, description: str = "", status: str = "pending", 
                   priority: str = "medium", due_date: Optional[str] = None) -> Dict:
        """
        Create a new task
        
        Args:
            title: Task title (required)
            description: Task description
            status: Task status (pending, in-progress, completed)
            priority: Task priority (low, medium, high)
            due_date: Due date in ISO format (YYYY-MM-DD)
            
        Returns:
            Dict containing the created task
        """
        url = f"{self.api_endpoint}/tasks"
        payload = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority
        }
        
        if due_date:
            payload["dueDate"] = due_date
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_all_tasks(self, status: Optional[str] = None) -> Dict:
        """
        Get all tasks, optionally filtered by status
        
        Args:
            status: Optional status filter (pending, in-progress, completed)
            
        Returns:
            Dict containing list of tasks and count
        """
        url = f"{self.api_endpoint}/tasks"
        params = {"status": status} if status else {}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_task(self, task_id: str) -> Dict:
        """
        Get a specific task by ID
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict containing the task details
        """
        url = f"{self.api_endpoint}/tasks/{task_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def update_task(self, task_id: str, **kwargs) -> Dict:
        """
        Update a task
        
        Args:
            task_id: The task ID
            **kwargs: Fields to update (title, description, status, priority, dueDate)
            
        Returns:
            Dict containing the updated task
        """
        url = f"{self.api_endpoint}/tasks/{task_id}"
        response = requests.put(url, json=kwargs)
        response.raise_for_status()
        return response.json()
    
    def delete_task(self, task_id: str) -> Dict:
        """
        Delete a task
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict containing success message
        """
        url = f"{self.api_endpoint}/tasks/{task_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()
    
    def upload_attachment(self, task_id: str, file_path: str) -> Dict:
        """
        Upload a file attachment to a task
        
        Args:
            task_id: The task ID
            file_path: Path to the file to upload
            
        Returns:
            Dict containing attachment details and download URL
        """
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        # Encode to base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Get filename
        import os
        file_name = os.path.basename(file_path)
        
        # Determine content type
        content_type = self._get_content_type(file_name)
        
        url = f"{self.api_endpoint}/tasks/{task_id}/attachments"
        payload = {
            "fileName": file_name,
            "fileContent": encoded_content,
            "contentType": content_type
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_attachments(self, task_id: str) -> Dict:
        """
        Get all attachments for a task
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict containing list of attachments with download URLs
        """
        url = f"{self.api_endpoint}/tasks/{task_id}/attachments"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def delete_attachment(self, task_id: str, file_id: str) -> Dict:
        """
        Delete an attachment
        
        Args:
            task_id: The task ID
            file_id: The file ID
            
        Returns:
            Dict containing success message
        """
        url = f"{self.api_endpoint}/tasks/{task_id}/attachments/{file_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()
    
    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        return content_types.get(ext, 'application/octet-stream')


def main():
    """Example usage of the API client"""
    
    # Replace with your actual API endpoint
    API_ENDPOINT = "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"
    
    # Initialize client
    client = TaskAPIClient(API_ENDPOINT)
    
    print("=== Serverless Task API - Python Client Example ===\n")
    
    # 1. Create a task
    print("1. Creating a new task...")
    task = client.create_task(
        title="Learn AWS Serverless",
        description="Master Lambda, API Gateway, and DynamoDB",
        status="in-progress",
        priority="high",
        due_date="2025-03-15"
    )
    print(f"   Created task: {task['taskId']}")
    print(f"   Title: {task['title']}\n")
    
    task_id = task['taskId']
    
    # 2. Get all tasks
    print("2. Fetching all tasks...")
    all_tasks = client.get_all_tasks()
    print(f"   Total tasks: {all_tasks['count']}\n")
    
    # 3. Get specific task
    print("3. Fetching task details...")
    task_details = client.get_task(task_id)
    print(f"   Status: {task_details['status']}")
    print(f"   Priority: {task_details['priority']}\n")
    
    # 4. Update task
    print("4. Updating task status...")
    updated_task = client.update_task(task_id, status="completed")
    print(f"   New status: {updated_task['status']}\n")
    
    # 5. Filter tasks by status
    print("5. Filtering completed tasks...")
    completed_tasks = client.get_all_tasks(status="completed")
    print(f"   Completed tasks: {completed_tasks['count']}\n")
    
    # 6. Delete task
    print("6. Deleting task...")
    result = client.delete_task(task_id)
    print(f"   {result['message']}\n")
    
    print("=== Example completed successfully! ===")


if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not installed")
        print("Install it with: pip install requests")
        exit(1)
    
    main()

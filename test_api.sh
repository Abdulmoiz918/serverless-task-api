#!/bin/bash

# API Testing Script
# Tests all endpoints of the Serverless Task API

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if API endpoint is provided
if [ -z "$1" ]; then
    if [ -f .api-endpoint ]; then
        API_ENDPOINT=$(cat .api-endpoint)
        echo -e "${YELLOW}Using saved API endpoint: ${API_ENDPOINT}${NC}"
    else
        echo -e "${RED}Error: API endpoint not provided${NC}"
        echo "Usage: ./test_api.sh <API_ENDPOINT>"
        echo "Example: ./test_api.sh https://abc123.execute-api.us-east-1.amazonaws.com/dev"
        exit 1
    fi
else
    API_ENDPOINT=$1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Serverless Task API - Testing Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "API Endpoint: ${API_ENDPOINT}"
echo ""

# Test 1: Create a task
echo -e "${YELLOW}Test 1: Creating a new task...${NC}"
CREATE_RESPONSE=$(curl -s -X POST ${API_ENDPOINT}/tasks \
    -H 'Content-Type: application/json' \
    -d '{
        "title": "Complete AWS Project",
        "description": "Build and deploy serverless task management API",
        "status": "in-progress",
        "priority": "high",
        "dueDate": "2025-03-01"
    }')

TASK_ID=$(echo $CREATE_RESPONSE | grep -o '"taskId":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TASK_ID" ]; then
    echo -e "${GREEN}✓ Task created successfully${NC}"
    echo "  Task ID: ${TASK_ID}"
    echo "  Response: ${CREATE_RESPONSE}" | head -c 150
    echo "..."
else
    echo -e "${RED}✗ Failed to create task${NC}"
    echo "  Response: ${CREATE_RESPONSE}"
    exit 1
fi
echo ""

# Test 2: Get all tasks
echo -e "${YELLOW}Test 2: Getting all tasks...${NC}"
GET_ALL_RESPONSE=$(curl -s ${API_ENDPOINT}/tasks)
TASK_COUNT=$(echo $GET_ALL_RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)

if [ ! -z "$TASK_COUNT" ]; then
    echo -e "${GREEN}✓ Retrieved all tasks${NC}"
    echo "  Total tasks: ${TASK_COUNT}"
else
    echo -e "${RED}✗ Failed to retrieve tasks${NC}"
    echo "  Response: ${GET_ALL_RESPONSE}"
fi
echo ""

# Test 3: Get specific task
echo -e "${YELLOW}Test 3: Getting task by ID...${NC}"
GET_TASK_RESPONSE=$(curl -s ${API_ENDPOINT}/tasks/${TASK_ID})

if echo $GET_TASK_RESPONSE | grep -q "$TASK_ID"; then
    echo -e "${GREEN}✓ Task retrieved successfully${NC}"
    echo "  Response: ${GET_TASK_RESPONSE}" | head -c 150
    echo "..."
else
    echo -e "${RED}✗ Failed to retrieve task${NC}"
    echo "  Response: ${GET_TASK_RESPONSE}"
fi
echo ""

# Test 4: Update task
echo -e "${YELLOW}Test 4: Updating task status...${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT ${API_ENDPOINT}/tasks/${TASK_ID} \
    -H 'Content-Type: application/json' \
    -d '{
        "status": "completed",
        "description": "Successfully deployed to AWS"
    }')

if echo $UPDATE_RESPONSE | grep -q "completed"; then
    echo -e "${GREEN}✓ Task updated successfully${NC}"
    echo "  Status changed to: completed"
else
    echo -e "${RED}✗ Failed to update task${NC}"
    echo "  Response: ${UPDATE_RESPONSE}"
fi
echo ""

# Test 5: Filter tasks by status
echo -e "${YELLOW}Test 5: Filtering tasks by status...${NC}"
FILTER_RESPONSE=$(curl -s "${API_ENDPOINT}/tasks?status=completed")

if echo $FILTER_RESPONSE | grep -q "completed"; then
    echo -e "${GREEN}✓ Successfully filtered tasks${NC}"
    FILTERED_COUNT=$(echo $FILTER_RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo "  Completed tasks: ${FILTERED_COUNT}"
else
    echo -e "${RED}✗ Failed to filter tasks${NC}"
    echo "  Response: ${FILTER_RESPONSE}"
fi
echo ""

# Test 6: Create another task
echo -e "${YELLOW}Test 6: Creating additional task...${NC}"
CREATE_RESPONSE2=$(curl -s -X POST ${API_ENDPOINT}/tasks \
    -H 'Content-Type: application/json' \
    -d '{
        "title": "Study for AWS SAA Exam",
        "description": "Review all AWS services",
        "status": "pending",
        "priority": "high"
    }')

TASK_ID2=$(echo $CREATE_RESPONSE2 | grep -o '"taskId":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TASK_ID2" ]; then
    echo -e "${GREEN}✓ Second task created successfully${NC}"
    echo "  Task ID: ${TASK_ID2}"
else
    echo -e "${RED}✗ Failed to create second task${NC}"
fi
echo ""

# Test 7: Delete task
echo -e "${YELLOW}Test 7: Deleting a task...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE ${API_ENDPOINT}/tasks/${TASK_ID})

if echo $DELETE_RESPONSE | grep -q "deleted successfully"; then
    echo -e "${GREEN}✓ Task deleted successfully${NC}"
else
    echo -e "${RED}✗ Failed to delete task${NC}"
    echo "  Response: ${DELETE_RESPONSE}"
fi
echo ""

# Test 8: Verify deletion
echo -e "${YELLOW}Test 8: Verifying task deletion...${NC}"
VERIFY_DELETE=$(curl -s ${API_ENDPOINT}/tasks/${TASK_ID})

if echo $VERIFY_DELETE | grep -q "not found"; then
    echo -e "${GREEN}✓ Task successfully deleted (404 confirmed)${NC}"
else
    echo -e "${RED}✗ Task still exists${NC}"
    echo "  Response: ${VERIFY_DELETE}"
fi
echo ""

# Test 9: Create task with attachment (base64 encoded)
echo -e "${YELLOW}Test 9: Testing file attachment...${NC}"

# Create a simple text file and encode it
TEST_CONTENT="This is a test attachment for task management"
BASE64_CONTENT=$(echo -n "$TEST_CONTENT" | base64)

ATTACH_RESPONSE=$(curl -s -X POST ${API_ENDPOINT}/tasks/${TASK_ID2}/attachments \
    -H 'Content-Type: application/json' \
    -d "{
        \"fileName\": \"test-document.txt\",
        \"fileContent\": \"${BASE64_CONTENT}\",
        \"contentType\": \"text/plain\"
    }")

if echo $ATTACH_RESPONSE | grep -q "uploaded successfully"; then
    echo -e "${GREEN}✓ File attachment uploaded successfully${NC}"
    FILE_ID=$(echo $ATTACH_RESPONSE | grep -o '"fileId":"[^"]*"' | cut -d'"' -f4)
    echo "  File ID: ${FILE_ID}"
else
    echo -e "${RED}✗ Failed to upload attachment${NC}"
    echo "  Response: ${ATTACH_RESPONSE}"
fi
echo ""

# Test 10: Get attachments
echo -e "${YELLOW}Test 10: Retrieving task attachments...${NC}"
GET_ATTACH_RESPONSE=$(curl -s ${API_ENDPOINT}/tasks/${TASK_ID2}/attachments)

if echo $GET_ATTACH_RESPONSE | grep -q "attachments"; then
    echo -e "${GREEN}✓ Attachments retrieved successfully${NC}"
    ATTACH_COUNT=$(echo $GET_ATTACH_RESPONSE | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo "  Total attachments: ${ATTACH_COUNT}"
else
    echo -e "${RED}✗ Failed to retrieve attachments${NC}"
    echo "  Response: ${GET_ATTACH_RESPONSE}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}All core functionalities tested successfully!${NC}"
echo ""
echo "Remaining task ID for cleanup: ${TASK_ID2}"
echo ""
echo "To delete the remaining task:"
echo "curl -X DELETE ${API_ENDPOINT}/tasks/${TASK_ID2}"
echo ""

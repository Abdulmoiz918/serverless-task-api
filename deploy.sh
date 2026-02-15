#!/bin/bash

# Serverless Task API - Deployment Script
# This script deploys the complete infrastructure to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="serverless-task-api"
ENVIRONMENT="dev"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-stack-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Serverless Task API Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Using AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Get region preference
read -p "Enter AWS Region (default: us-east-1): " input_region
REGION=${input_region:-$REGION}
echo -e "${GREEN}✓ Using Region: ${REGION}${NC}"
echo ""

# Create deployment package
echo -e "${YELLOW}Creating deployment packages...${NC}"

# Create temp directory
rm -rf deployment_packages
mkdir -p deployment_packages

# Package Task Handler
echo "Packaging task_handler..."
cd deployment_packages
mkdir -p task_handler
cp ../task_handler.py task_handler/
cd task_handler
zip -r ../task_handler.zip . > /dev/null
cd ..
rm -rf task_handler
echo -e "${GREEN}✓ Task handler packaged${NC}"

# Package Attachment Handler
echo "Packaging attachment_handler..."
mkdir -p attachment_handler
cp ../attachment_handler.py attachment_handler/
cd attachment_handler
zip -r ../attachment_handler.zip . > /dev/null
cd ..
rm -rf attachment_handler
echo -e "${GREEN}✓ Attachment handler packaged${NC}"
cd ..

echo ""

# Deploy CloudFormation stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"
echo "Stack Name: ${STACK_NAME}"
echo ""

aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides \
        ProjectName=${PROJECT_NAME} \
        Environment=${ENVIRONMENT} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CloudFormation stack deployed successfully${NC}"
else
    echo -e "${RED}Error: CloudFormation deployment failed${NC}"
    exit 1
fi

echo ""

# Get stack outputs
echo -e "${YELLOW}Retrieving stack outputs...${NC}"
TASK_FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`TaskLambdaFunctionName`].OutputValue' \
    --output text \
    --region ${REGION})

ATTACHMENT_FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`AttachmentLambdaFunctionName`].OutputValue' \
    --output text \
    --region ${REGION})

API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text \
    --region ${REGION})

echo -e "${GREEN}✓ Stack outputs retrieved${NC}"
echo ""

# Update Lambda functions with actual code
echo -e "${YELLOW}Updating Lambda functions with code...${NC}"

echo "Updating task handler function..."
aws lambda update-function-code \
    --function-name ${TASK_FUNCTION_NAME} \
    --zip-file fileb://deployment_packages/task_handler.zip \
    --region ${REGION} > /dev/null

echo -e "${GREEN}✓ Task handler updated${NC}"

echo "Updating attachment handler function..."
aws lambda update-function-code \
    --function-name ${ATTACHMENT_FUNCTION_NAME} \
    --zip-file fileb://deployment_packages/attachment_handler.zip \
    --region ${REGION} > /dev/null

echo -e "${GREEN}✓ Attachment handler updated${NC}"

# Wait for functions to be ready
echo ""
echo -e "${YELLOW}Waiting for Lambda functions to be ready...${NC}"
sleep 10

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "API Endpoint: ${GREEN}${API_ENDPOINT}${NC}"
echo ""
echo "Example API calls:"
echo ""
echo "1. Create a task:"
echo "   curl -X POST ${API_ENDPOINT}/tasks \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"title\":\"My First Task\",\"description\":\"Test task\",\"status\":\"pending\"}'"
echo ""
echo "2. Get all tasks:"
echo "   curl ${API_ENDPOINT}/tasks"
echo ""
echo "3. Get task by ID:"
echo "   curl ${API_ENDPOINT}/tasks/{taskId}"
echo ""
echo "4. Update task:"
echo "   curl -X PUT ${API_ENDPOINT}/tasks/{taskId} \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"status\":\"completed\"}'"
echo ""
echo "5. Delete task:"
echo "   curl -X DELETE ${API_ENDPOINT}/tasks/{taskId}"
echo ""
echo -e "${YELLOW}Note: Replace {taskId} with an actual task ID${NC}"
echo ""
echo "To test the API, run: ./test_api.sh ${API_ENDPOINT}"
echo ""
echo -e "${GREEN}Happy coding!${NC}"

# Save endpoint to file for testing
echo ${API_ENDPOINT} > .api-endpoint

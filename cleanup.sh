#!/bin/bash

# Cleanup Script - Deletes all AWS resources created by this project
# Use with caution!

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_NAME="serverless-task-api"
ENVIRONMENT="dev"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-stack-${ENVIRONMENT}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}AWS Resource Cleanup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${RED}WARNING: This will delete ALL resources created by this project!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Get region
read -p "Enter AWS Region (default: us-east-1): " input_region
REGION=${input_region:-$REGION}
echo ""

echo -e "${YELLOW}Checking if stack exists...${NC}"

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} &> /dev/null; then
    echo -e "${RED}Stack ${STACK_NAME} not found in region ${REGION}${NC}"
    exit 1
fi

# Get S3 bucket name from stack
echo -e "${YELLOW}Getting S3 bucket name...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`AttachmentsBucketName`].OutputValue' \
    --output text \
    --region ${REGION})

if [ ! -z "$BUCKET_NAME" ]; then
    echo -e "${GREEN}Found bucket: ${BUCKET_NAME}${NC}"
    
    # Empty the S3 bucket
    echo -e "${YELLOW}Emptying S3 bucket...${NC}"
    aws s3 rm s3://${BUCKET_NAME} --recursive --region ${REGION}
    echo -e "${GREEN}✓ S3 bucket emptied${NC}"
else
    echo -e "${YELLOW}No S3 bucket found or already deleted${NC}"
fi

echo ""

# Delete CloudFormation stack
echo -e "${YELLOW}Deleting CloudFormation stack...${NC}"
aws cloudformation delete-stack \
    --stack-name ${STACK_NAME} \
    --region ${REGION}

echo -e "${GREEN}✓ Delete initiated${NC}"
echo ""
echo -e "${YELLOW}Waiting for stack deletion to complete...${NC}"
echo "This may take a few minutes..."

aws cloudformation wait stack-delete-complete \
    --stack-name ${STACK_NAME} \
    --region ${REGION}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All resources have been deleted:"
echo "  - Lambda functions"
echo "  - API Gateway"
echo "  - DynamoDB table"
echo "  - S3 bucket"
echo "  - IAM roles"
echo "  - CloudWatch logs (will be auto-deleted after retention period)"
echo ""
echo -e "${GREEN}Your AWS account is now clean!${NC}"
echo ""

# Remove local deployment artifacts
if [ -d "deployment_packages" ]; then
    rm -rf deployment_packages
    echo "Local deployment packages cleaned up"
fi

if [ -f ".api-endpoint" ]; then
    rm .api-endpoint
    echo "API endpoint file removed"
fi

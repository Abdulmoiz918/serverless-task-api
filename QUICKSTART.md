# Quick Start Guide - Serverless Task API

## 📋 Prerequisites Checklist

Before you begin, make sure you have:

- [ ] An AWS account (free tier is sufficient)
- [ ] AWS CLI installed on your computer
- [ ] Basic knowledge of command line/terminal
- [ ] A text editor (VS Code, Sublime, or any editor)

## 🔧 Step 1: Install AWS CLI

### For Windows:
1. Download the AWS CLI installer from: https://aws.amazon.com/cli/
2. Run the downloaded MSI installer
3. Follow the installation wizard

### For macOS:
```bash
# Using Homebrew
brew install awscli

# Or using pip
pip3 install awscli
```

### For Linux:
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Verify Installation:
```bash
aws --version
```
You should see something like: `aws-cli/2.x.x Python/3.x.x ...`

## 🔑 Step 2: Configure AWS Credentials

1. **Log in to AWS Console** (https://console.aws.amazon.com)

2. **Create an IAM User** (if you don't have one):
   - Go to IAM → Users → Add User
   - Username: `serverless-developer`
   - Access type: ✅ Programmatic access
   - Permissions: Attach `AdministratorAccess` policy (for learning)
   - Create user and **save the Access Key ID and Secret Access Key**

3. **Configure AWS CLI**:
   ```bash
   aws configure
   ```
   
   Enter your details:
   ```
   AWS Access Key ID: [Your Access Key]
   AWS Secret Access Key: [Your Secret Key]
   Default region name: us-east-1
   Default output format: json
   ```

4. **Test your credentials**:
   ```bash
   aws sts get-caller-identity
   ```
   
   You should see your account information.

## 📥 Step 3: Download the Project

### Option A: Clone from GitHub
```bash
git clone https://github.com/yourusername/serverless-task-api.git
cd serverless-task-api
```

### Option B: Download ZIP
1. Download the ZIP file from GitHub
2. Extract it to a folder
3. Open terminal and navigate to the folder:
   ```bash
   cd path/to/serverless-task-api
   ```

## 🚀 Step 4: Deploy to AWS

### Make Scripts Executable (Linux/Mac):
```bash
chmod +x deploy.sh test_api.sh cleanup.sh
```

### For Windows Users:
If using Git Bash or WSL:
```bash
bash deploy.sh
```

If using PowerShell, you'll need to run AWS CLI commands manually or install Git Bash.

### Deploy the Project:
```bash
./deploy.sh
```

**What happens during deployment:**
1. ✅ Checks your AWS credentials
2. ✅ Packages Lambda functions
3. ✅ Creates CloudFormation stack (this creates all AWS resources)
4. ✅ Updates Lambda functions with code
5. ✅ Displays your API endpoint

**Expected output:**
```
========================================
Deployment Complete!
========================================

API Endpoint: https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev

Example API calls:
1. Create a task:
   curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/tasks ...
```

**⏱️ Deployment time:** 3-5 minutes

**💰 Cost:** $0 (covered by AWS Free Tier)

## ✅ Step 5: Test Your API

### Automatic Testing:
```bash
./test_api.sh
```

This will run 10 automated tests and show you the results.

### Manual Testing with curl:

**1. Create a task:**
```bash
curl -X POST https://YOUR-API-ENDPOINT/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "My First Task",
    "description": "Testing the API",
    "status": "pending",
    "priority": "high"
  }'
```

**2. Get all tasks:**
```bash
curl https://YOUR-API-ENDPOINT/tasks
```

**3. Get tasks by status:**
```bash
curl https://YOUR-API-ENDPOINT/tasks?status=pending
```

### Test with Postman (GUI Tool):

1. Download Postman: https://www.postman.com/downloads/
2. Create a new collection called "Task API"
3. Add requests:
   - POST `https://YOUR-API-ENDPOINT/tasks`
   - GET `https://YOUR-API-ENDPOINT/tasks`
   - GET `https://YOUR-API-ENDPOINT/tasks/{taskId}`
   - PUT `https://YOUR-API-ENDPOINT/tasks/{taskId}`
   - DELETE `https://YOUR-API-ENDPOINT/tasks/{taskId}`

## 🔍 Step 6: View Your Resources in AWS

### 1. Lambda Functions:
- Go to AWS Console → Lambda
- You'll see: `serverless-task-api-task-handler-dev` and `serverless-task-api-attachment-handler-dev`
- Click on them to see the code and configuration

### 2. API Gateway:
- Go to AWS Console → API Gateway
- You'll see: `serverless-task-api-api-dev`
- Click on it to see all your endpoints

### 3. DynamoDB:
- Go to AWS Console → DynamoDB → Tables
- You'll see: `serverless-task-api-tasks-dev`
- Click "Explore items" to see your tasks

### 4. S3:
- Go to AWS Console → S3
- You'll see: `serverless-task-api-attachments-XXXX-dev`
- This is where file attachments are stored

### 5. CloudWatch Logs:
- Go to AWS Console → CloudWatch → Log groups
- You'll see logs for your Lambda functions
- Click on them to see execution logs

## 🎓 Learning Activities

### Activity 1: Modify a Lambda Function
1. Go to Lambda console
2. Open `serverless-task-api-task-handler-dev`
3. Scroll to the code section
4. Add a print statement: `print("Hello from Lambda!")`
5. Click "Deploy"
6. Create a task via API
7. Check CloudWatch Logs to see your message

### Activity 2: Add a New Field to Tasks
1. Modify `task_handler.py` locally
2. Add support for a `tags` field
3. Redeploy: `./deploy.sh`
4. Test the new field

### Activity 3: Monitor with CloudWatch
1. Create 10 tasks using the test script
2. Go to CloudWatch → Dashboards
3. Create a custom dashboard
4. Add metrics for Lambda invocations

## 🗑️ Step 7: Cleanup (When Done)

**Important:** To avoid any charges, clean up when you're done learning.

```bash
./cleanup.sh
```

This will:
- Empty the S3 bucket
- Delete all AWS resources
- Remove the CloudFormation stack

**Verify cleanup:**
- Check Lambda console (should be empty)
- Check DynamoDB console (table should be gone)
- Check S3 console (bucket should be deleted)

## 🆘 Troubleshooting

### Issue: "AccessDenied" error
**Solution:** Your IAM user needs more permissions. Attach `AdministratorAccess` policy.

### Issue: "Stack already exists"
**Solution:** The stack name is taken. Either:
1. Delete the existing stack in CloudFormation console
2. Or modify the STACK_NAME in `deploy.sh`

### Issue: "Command not found: aws"
**Solution:** AWS CLI is not installed or not in PATH. Reinstall AWS CLI.

### Issue: "Region 'None' not found"
**Solution:** Run `aws configure` and set a region (e.g., us-east-1)

### Issue: Deployment fails at CloudFormation
**Solution:** 
1. Check CloudFormation console for error details
2. Common cause: S3 bucket name already taken (must be globally unique)
3. Run `./cleanup.sh` and try again

### Issue: Lambda function times out
**Solution:** This shouldn't happen with our simple functions, but if it does:
1. Check CloudWatch Logs for errors
2. Increase Lambda timeout in `cloudformation-template.yaml`

## 📚 Next Steps

### 1. Enhance the Project:
- Add authentication (AWS Cognito)
- Add a frontend (React + Amplify)
- Add email notifications (SNS)
- Add search functionality (ElasticSearch)
- Add caching (ElastiCache)

### 2. Learn More AWS:
- AWS Lambda best practices
- DynamoDB data modeling
- API Gateway authorizers
- CloudWatch custom metrics
- AWS SAM (Serverless Application Model)

### 3. Prepare for AWS SAA:
- Review all services used in this project
- Understand why we chose each service
- Practice explaining the architecture
- Read AWS Well-Architected Framework

## 🎯 Common Beginner Questions

**Q: Do I need a credit card for AWS?**
A: Yes, but you won't be charged if you stay within Free Tier limits.

**Q: How long can I run this for free?**
A: 12 months under AWS Free Tier for new accounts.

**Q: Can I break something and get charged a lot?**
A: Very unlikely with this project. Set up billing alerts at $1, $5, $10.

**Q: What if I get stuck?**
A: 
1. Check AWS CloudFormation console for error messages
2. Check CloudWatch Logs
3. Google the exact error message
4. Ask on AWS forums or Reddit r/aws

**Q: Do I need to know Python?**
A: Basic Python helps, but you can learn as you go. The code is well-commented.

**Q: Can I use this project for my resume?**
A: Absolutely! That's what it's designed for. See PROJECT_SUMMARY.md for resume tips.

## ✅ Success Checklist

After completing this guide, you should be able to:

- [ ] Deploy AWS resources using CloudFormation
- [ ] Create and update Lambda functions
- [ ] Configure API Gateway
- [ ] Use DynamoDB for data storage
- [ ] Upload files to S3
- [ ] Monitor with CloudWatch
- [ ] Clean up AWS resources
- [ ] Explain serverless architecture
- [ ] Add this project to your resume

## 🎉 Congratulations!

You've successfully deployed a production-grade serverless application on AWS!

**What you've learned:**
✅ Serverless architecture
✅ Infrastructure as Code
✅ AWS Lambda
✅ API Gateway
✅ DynamoDB
✅ S3
✅ CloudWatch
✅ IAM

**Next:** Study for your AWS SAA exam and add this to your resume!

---

Need help? Create an issue on GitHub or reach out!
Good luck with your AWS certification! 🚀

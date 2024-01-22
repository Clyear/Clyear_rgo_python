import os
import time
import json
import utils
import boto3
import logging

logger = logging.getLogger()

# Private lambda - doesn't return http response
def handle(event):
    s3_http_file_path = event.get('filePath')
    document_name = s3_http_file_path.replace(utils.S3_HOME, '', 1)
    try:
      
        
        # Start expense analysis
        
        expense_job_id = analyse_expense(document_name)
  
            
        print(f'Expense analysis started with job id: {expense_job_id}')
    except Exception as error:
        print(f'Unable to start expense analysis, {str(error)}')
        utils.notify_backend_on_failure( event.get('senderEmail') , 'Unable to start expense analysis', 'E0001', document_name )
        raise error

    return {
        'expenseJobId': expense_job_id
    }


# Start expense analysis
def analyse_expense(document_name):
    document_location = {
        'S3Object': {
            'Bucket': utils.BUCKET_NAME,
            'Name': document_name
        }
    }
    
    textract_client = boto3.client('textract')
    expense_response = textract_client.start_expense_analysis(
        DocumentLocation = document_location,
        NotificationChannel = {
            "SNSTopicArn": "arn:aws:sns:us-east-1:637423465315:AmazonTextractDocumentAnalysis",
            "RoleArn": "arn:aws:iam::637423465315:role/AWSTextract-SNSPublishRole"
        }
    )
    expense_job_id = expense_response.get('JobId')
    logging.info(f'Expense analysis job started: JobId: {expense_job_id}')
    
    return expense_job_id
   
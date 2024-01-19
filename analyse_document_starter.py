import os
import time
import json
import utils
import boto3
import logging


logger = logging.getLogger()

# Private lambda - doesn't return http response
def handle(event, context):
    document_name = event.get('documentName', None)
    result_file_path = get_s3_file_path(event)
    
    try:
     
        document_job_id = analyse_document(document_name)
        print(f'Document analysis started with job id: {document_job_id}')
       
        
        # Start expense analysis
        # expense_job_id = analyse_expense(document_name)
        # print(f'Expense analysis started with job id: {expense_job_id}')
    except Exception as error:
        print(f'Unable to start document analysis, {str(error)}')
        utils.notify_backend_on_failure( event.get('senderEmail') , 'Unable to start document analysis', 'E0001', document_name,event.get('receiverEmail') )
        raise error

    return {
        'analysisJobId': document_job_id
        # 'expenseJobId': expense_job_id
    }


# Start document analysis
def analyse_document(document_name):
    document_location = {
        'S3Object': {
            'Bucket': utils.BUCKET_NAME,
            'Name': document_name
        }
    }
    textract_client = boto3.client('textract')
    
    document_response = textract_client.start_document_analysis(
        DocumentLocation = document_location,
        FeatureTypes = ['FORMS'],
        NotificationChannel = {
            "SNSTopicArn": "arn:aws:sns:us-east-1:334397713756:AmazonTextractDocumentAnalysis",
            "RoleArn": "arn:aws:iam::334397713756:role/AWSTextract-SNSPublishRole"
        }
    )
    document_job_id = document_response.get('JobId')
    logging.info(f'Document analysis job started: JobId: {document_job_id}')
    
    return document_job_id


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
            "SNSTopicArn": "arn:aws:sns:us-east-1:755262417782:AmazonTextractExpenseAnalysis",
            "RoleArn": "arn:aws:iam::755262417782:role/AWSTextract-SNSPublishRole"
        }
    )
    expense_job_id = expense_response.get('JobId')
    logging.info(f'Expense analysis job started: JobId: {expense_job_id}')
    
    return expense_job_id


def get_s3_file_path(event):
    folder_name = event.get('folderName')
    file_name = event.get('fileName')

    file_root, file_ext = os.path.splitext(file_name)
    file_type = file_ext.split('.')[1]
    analysis_result_file = f'{file_root}.{file_type}-textracted.json'
    analysis_result_file_path = f'{analysis_result_file}'

    return f'{folder_name}/{analysis_result_file}'
    
    
 
# def checkdocument(Keys):

#     document_status=''
#     client = boto3.client('s3')

#     response=client.get_object(Bucket=utils.BUCKET_NAME,Key=Keys)

#     data=response['Body'].read()
#     # print(data)
#     # pdf = PdfFileReader(BytesIO(data))
#     # print(pdf)
#     try:
#         pdf = PdfFileReader(BytesIO(data))
#         document_status=True

#     except:
#         document_status=False
#         pass
#     print(document_status)
#     return document_status


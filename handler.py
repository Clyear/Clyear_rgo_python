import os
import time
import json
import utils
import boto3
import document_analysis_handler
import expense_analysis_handler

# Private lambda - doesn't return http response
def handle(event, context):
    print(f'Event from SNS topic: {event}')
    
    sns_message = get_sns_message(event)
    api = sns_message.get('API')
    s3_object_name = sns_message.get('DocumentLocation', {}).get('S3ObjectName')
    analysis_job_id = sns_message.get('JobId')
    print(f'Analysis job id found for {api} is {analysis_job_id}')
    
    if api == 'StartDocumentAnalysis':
        document_analysis_handler.handle(analysis_job_id, s3_object_name)
    elif api == 'StartExpenseAnalysis':
        expense_analysis_handler.handle(analysis_job_id, s3_object_name)
    
    return None

# Gets message from SNS event
def get_sns_message(event):
    sns_event = event['Records'][0]['Sns']
    sns_message_str = sns_event.get('Message', '{}')
    sns_message = json.loads(sns_message_str)
    return sns_message

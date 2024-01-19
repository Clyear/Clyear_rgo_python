import os
import json
import requests

# Environment variables
NODE_EXTRACTION_URL = os.getenv('NODE_EXTRACTION_URL')
AUTH_HEADER = os.getenv('AUTH_HEADER')
BUCKET_NAME = os.getenv('BUCKET_NAME')
BUCKET_REGION = os.getenv('BUCKET_REGION')

# Supportive constants
S3_HOME = f'https://{BUCKET_NAME}.s3.amazonaws.com/'

# Supportive constants
SUPPORTED_FILE_EXT = ['.png', '.jpg', '.jpeg', '.pdf', '.tiff']
SUPPORTED_PDF_CONVERSIONS = ['.png', '.jpg', '.jpeg', '.tiff']

# Node APIs
SAVE_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/saveInvoice'
UPDATE_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/updateInvoice'
EXCEPTION_NOTIFY_URL = f'{NODE_EXTRACTION_URL}/invoice/invoiceErrorHandle'
GET_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceById?invoiceId='
DELETE_EXPENSE_URL=f'{NODE_EXTRACTION_URL}/invoice/deleteExpenseList?invoiceId='

# Node API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

# Helper functions
def create_response(status_code, content):
    if status_code == 200:
        return create_200_response(content)
    else:
        return create_error_response(status_code, content)

def create_200_response(content):
    return {
        'statusCode': 200,
        'body': json.dumps(content)
    }

def create_error_response(status_code, message):
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'error': message
        })
    }
    
# make update API call with filepath and error messages to show failure in lambda
def notify_backend_on_failure(senderEmail, msg, code, filepath,receiverEmail):
    print(f'Notifying backend on failure of {filepath}')
    data = {
        'isSuccess': False,
        'errorMessage': msg,
        'errorCode': code,
        'senderEmail': senderEmail,
        'filePath': filepath,
        "receiverEmail":receiverEmail
    }
    response = requests.put(url = EXCEPTION_NOTIFY_URL, data=json.dumps(data), headers=API_V2_HEADER)
    print(f'Notified backend: {response}')

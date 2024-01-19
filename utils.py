import os

# Environment variables
BUCKET_NAME = os.getenv('BUCKET_NAME')
BUCKET_REGION = os.getenv('BUCKET_REGION')
NODE_EXTRACTION_URL = os.getenv('NODE_EXTRACTION_URL')
AUTH_HEADER = os.getenv('AUTH_HEADER')

# Supportive constants
S3_HOME = f'https://{BUCKET_NAME}.s3.amazonaws.com/'

# Node APIs
GET_EXTRACTED_LABELS_URL = f'{NODE_EXTRACTION_URL}/invoice/getExtractedLabels?invoiceId='
SAVE_EXTRACTED_LABEL_URL = f'{NODE_EXTRACTION_URL}/invoice/saveExtractedLabels'
UPDATE_EXTRACTED_LABEL_URL = f'{NODE_EXTRACTION_URL}/invoice/updateExtractedLabels'

# Node API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}
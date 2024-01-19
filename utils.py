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

# Node APIs
FIND_SUPPLIER_URL = f'{NODE_EXTRACTION_URL}/invoice/getSupplierDetails'
EXCEPTION_NOTIFY_URL = f'{NODE_EXTRACTION_URL}/invoice/invoiceErrorHandle'

# Node API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

# make update API call with filepath and error messages to show failure in lambda
def notify_backend_on_failure(senderEmail, msg, code, filePath,receiverEmail):
    print(f'Notifying backend on failure of {filePath}')
    data = { 
        'isSuccess': False, 
        'errorMessage': msg, 
        'errorCode': code,
        'senderEmail': senderEmail, 
        'filePath': filePath,
        "receiverEmail":receiverEmail 
    }
    response = requests.put(url = EXCEPTION_NOTIFY_URL, data=json.dumps(data), headers= API_V2_HEADER)
    print(f'Notified backend: {response}')
    print(f'request: {data}')




def notify_backend_on_failure1(receiverEmail, msg, code, filePath,subjects,from_email,emailreceviestime):
    print(f'Notifying backend on failure of {filePath}')
    # timezome='US/Eastern'

    # est=pytz.timezone(timezome)

    # print(datetime.now(est))
    # receivedTime=datetime.now(est)
    data = { 
        'isSuccess': False, 
        'errorMessage': msg, 
        'errorCode': code,
        'receivedTime':str(emailreceviestime),
        'timeZone':'EST',
        'emailSubject':subjects,
        'senderEmail':from_email,
        
        
        'filePath': filePath ,
        'receiverEmail': receiverEmail
    }
    response = requests.put(url = EXCEPTION_NOTIFY_URL, data=json.dumps(data), headers= API_V2_HEADER)
    print(f'Notified backend: {response}')
    print(f'request: {data}')


file_extensions = [
    ".txt", ".doc", ".docx", ".pdf",
    ".xls", ".xlsx", ".csv",
    ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".mp3", ".wav", ".ogg",
    ".mp4", ".avi", ".mkv",
    ".zip", ".rar", ".tar.gz", ".7z",
    ".c", ".cpp", ".java", ".py", ".html", ".css", ".js",
    ".db",
    ".exe", ".app", ".sh",
    ".ttf", ".otf",
    ".dll", ".sys", ".conf",
    ".epub", ".mobi",
    ".json", ".xml"
]

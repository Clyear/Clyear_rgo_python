import json
import boto3
import utils
import logging
import requests
import time
from urllib.parse import quote

# Private lambda - doesn't return http response
def handle(event):
    invoice_id = event.get('invoiceId')
    vendor_name = event.get('name')
    orgId=event.get('orgId')
    document_data_path = event.get('documentDataPath')
    
    if document_data_path is None or document_data_path == "":
        logging.error('Document data path not found')
        raise ValueError('Document data path not found')

    detected_entities = None
    try:
        document_data = read_document_data(document_data_path)
        print(document_data)
        detected_entities = detect_document_entities(document_data, vendor_name,orgId)
    except Exception as error:
        logging.error(str(error))
        raise ValueError(error)

    print(detected_entities)
    return detected_entities
    
def read_document_data(document_data_path):
    # Get S3 object handle
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_data_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = document_data_path
    )
    
    # Read document data from S3
    document_data_str = document_data_s3_response.get('Body').read()
    document_data = json.loads(document_data_str)
    print('documentdata',document_data.get('documentData'))
    return document_data.get('documentData')

def detect_document_entities(document_data, vendor_name,orgId):
    logging.info('Detecting entities from the document data..')
    
    
    # logger = logging.getLogger()
    # try: # for Python 3
    #     from http.client import HTTPConnection
    # except ImportError:
    #     from httplib import HTTPConnection
    # HTTPConnection.debuglevel = 1
    
    # logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True
    
    # print('request',requests.get('https://httpbin.org/headers'))

    # Detect entities from document data with label and value
    # for i in range (2):
    # detect_entities_request = {
    #     'vendorName':vendor_name,
    #     'datasetType': 'Invoice',
    #     'phraseList': list(document_data.keys()),
    #     'orgId':orgId
    # }
        # print(detect_entities_request)
        
        
    params = {
    'vendorName': vendor_name,
    'datasetType': 'Invoice',
    
    'orgId':orgId
    }
    phraseList=list(document_data.keys())

    response = requests.get(
    url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
    headers=utils.API_V2_HEADER,
    params=params)
    if response.status_code==403:
        return {}
    if response.status_code!=200:
        return {}

    payload_data=response.json()
    payload_data['phraseList']=phraseList
    print(response.elapsed.total_seconds())
    
    print(payload_data)
    
       
    detected_entities_response = requests.post(
    url = utils.DETECT_ENTITIES_URL,
    data = json.dumps(payload_data)
    
    
    )
    print(detected_entities_response,'below 5 seconds')
    # print(json.dumps(detect_entities_request))
    
        # if detected_entities_response.status_code==200:
        #     break
        # else:
        #     time.sleep(3)
        #     continue
        

 
        

    if detected_entities_response.status_code == 500:
        return {}

    if detected_entities_response.status_code != 200:
        print('Unable to predict invoice entities from the document')
        return {}
        # raise ValueError('Unable to predict invoice entities from the document')

    detected_entities = detected_entities_response.json()
    print(detected_entities)
    
    entity_label_dict = {}
    for entity_name, label in detected_entities.items():
        entity_label_dict[entity_name] = {
            'label': label,
            'value': document_data[label]
        }
    
    logging.info('Entities detected from the document data..')
    return entity_label_dict
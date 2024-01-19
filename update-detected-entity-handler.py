import json
import boto3
import utils
import requests
import logging
import get_extracted_label_handler
import create_extracted_label_handler
import update_extracted_label_handler

def handle(event, context):
    print(event)

    # request_method = event.get('requestContext', {}).get('http', {}).get('method')
    # if request_method == 'OPTIONS':
    #     return
    try:
        request_event = event.get('body')
        print(request_event)
        res = json.loads(request_event)
        invoice_id = res.get('invoiceId')
        updated_entities = res.get('entityDatasetDetails')
        create_update_invoice_labels(invoice_id, updated_entities)
        
        
        # convertjson(event)
    except Exception as ex:
        logging.exception(ex)
        return {
        'body': json.dumps({
            'success': True
        }),
        'statusCode': 200
    }
    invoice_id = res.get('invoiceId')
    updated_entities = res.get('entityDatasetDetails')
    create_update_invoice_labels(invoice_id, updated_entities)
    
    return {
        'body': json.dumps({
            'success': True
        }),
        'statusCode': 200
    }
    
def convertjson(event):
    print(event['body'])
    
    request_event=event['body']
    print(request_event)
    # res = json.loads(request_event)
    test_string = '{"Nikhil" : 1, "Akshat" : 2, "Akash" : 3}'
    res = json.loads(request_event)
    print(res)
    # print(event[''])

def create_update_invoice_labels(invoice_id, updated_entities):
    print('invoice_id',invoice_id, 'updated_entities',updated_entities )
    invoice_labels = get_extracted_label_handler.handle(invoice_id)
    print(invoice_labels,'invoice_labels')

    save_labels = []
    update_labels = []
    for entity in updated_entities:
        print(entity,type(entity))
        
        field_name = entity.get('extractedLabel')
        print('field_name',field_name)
        target_variable = entity.get('invoiceLabel')
        print(target_variable,'target_variable')
        invoice_label = invoice_labels.get(target_variable,None)
        
        if invoice_label is None:
            save_labels.append({
                'labelType': target_variable,
                'label': field_name,
                'detectedLabel': 'N/A'
            })
        else:
            update_labels.append({
                'labelType': target_variable,
                'label': field_name,
                'detectedLabel': invoice_label.get('detectedLabel')
            })

    print(f'New labels chosen by user {save_labels}')
    print(f'Existing labels modified by user {update_labels}')
    
    if len(save_labels) > 0:
        create_extracted_label_handler.handle({
            'invoiceId': invoice_id,
            'invoiceLabels': save_labels
        })
    if len(update_labels) > 0:
        update_extracted_label_handler.handle({
            'invoiceId': invoice_id,
            'invoiceLabels': update_labels
        })

    return None
  
# event={'version': '1.0', 'resource': '/test-function', 'path': '/default/test-function', 'httpMethod': 'POST', 'headers': {'Content-Length': '1061', 'Content-Type': 'application/json', 'Host': 'agfv7rujrd.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 'X-Amzn-Trace-Id': 'Root=1-639c46d1-16e88c403285bd920ffa6f3a', 'X-Forwarded-For': '157.49.88.119', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'accept': 'application/json, text/plain, */*', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-US,en;q=0.9', 'authorization': '23a39ff1f2aeb5c0860f854b347a752f7d0fc902d201de03ae81cb82669ca89548edfb55e59231c1052ac46fb07bdb1594205e4a3bb0c9b2e7d0073ba0bf342cb0937b2164efbe2114cbbaf470a5d975f485e0136cdd1d63c1bf2b4b791e6dff1eb30efbcb532bebc957fb0f9d4de64ac781edcf4464631648bf11b7be7b86c6104b62c727bc02114baa6fccf0375e9463e656d4870f256570b2136727328c28e774cc3543d7c36a29fbdd7a6bdc7341', 'origin': 'http://localhost:3000', 'referer': 'http://localhost:3000/', 'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'cross-site'}, 'multiValueHeaders': {'Content-Length': ['1061'], 'Content-Type': ['application/json'], 'Host': ['agfv7rujrd.execute-api.us-east-1.amazonaws.com'], 'User-Agent': ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'], 'X-Amzn-Trace-Id': ['Root=1-639c46d1-16e88c403285bd920ffa6f3a'], 'X-Forwarded-For': ['157.49.88.119'], 'X-Forwarded-Port': ['443'], 'X-Forwarded-Proto': ['https'], 'accept': ['application/json, text/plain, */*'], 'accept-encoding': ['gzip, deflate, br'], 'accept-language': ['en-US,en;q=0.9'], 'authorization': ['23a39ff1f2aeb5c0860f854b347a752f7d0fc902d201de03ae81cb82669ca89548edfb55e59231c1052ac46fb07bdb1594205e4a3bb0c9b2e7d0073ba0bf342cb0937b2164efbe2114cbbaf470a5d975f485e0136cdd1d63c1bf2b4b791e6dff1eb30efbcb532bebc957fb0f9d4de64ac781edcf4464631648bf11b7be7b86c6104b62c727bc02114baa6fccf0375e9463e656d4870f256570b2136727328c28e774cc3543d7c36a29fbdd7a6bdc7341'], 'origin': ['http://localhost:3000'], 'referer': ['http://localhost:3000/'], 'sec-ch-ua': ['"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"'], 'sec-ch-ua-mobile': ['?0'], 'sec-ch-ua-platform': ['"Windows"'], 'sec-fetch-dest': ['empty'], 'sec-fetch-mode': ['cors'], 'sec-fetch-site': ['cross-site']}, 'queryStringParameters': None, 'multiValueQueryStringParameters': None, 'requestContext': {'accountId': '328326462997', 'apiId': 'agfv7rujrd', 'domainName': 'agfv7rujrd.execute-api.us-east-1.amazonaws.com', 'domainPrefix': 'agfv7rujrd', 'extendedRequestId': 'dPAAsgWeIAMEZCw=', 'httpMethod': 'POST', 'identity': {'accessKey': None, 'accountId': None, 'caller': None, 'cognitoAmr': None, 'cognitoAuthenticationProvider': None, 'cognitoAuthenticationType': None, 'cognitoIdentityId': None, 'cognitoIdentityPoolId': None, 'principalOrgId': None, 'sourceIp': '157.49.88.119', 'user': None, 'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 'userArn': None}, 'path': '/default/test-function', 'protocol': 'HTTP/1.1', 'requestId': 'dPAAsgWeIAMEZCw=', 'requestTime': '16/Dec/2022:10:22:09 +0000', 'requestTimeEpoch': 1671186129026, 'resourceId': 'ANY /test-function', 'resourcePath': '/test-function', 'stage': 'default'}, 'pathParameters': None, 'stageVariables': None, 'body': '{"invoiceId":21,"entityDatasetDetails":[{"extractedLabel":"","InvoiceLabel":"invoiceNumber"},{"extractedLabel":"","InvoiceLabel":"dueDate"},{"extractedLabel":"","InvoiceLabel":"invoiceAmount"},{"extractedLabel":"","InvoiceLabel":"dueAmount"},{"extractedLabel":"","InvoiceLabel":"orderNumber"},{"extractedLabel":"","InvoiceLabel":"invoiceDate"},{"extractedLabel":"","InvoiceLabel":"taxTotal"},{"extractedLabel":"","InvoiceLabel":"quantity"},{"extractedLabel":"","InvoiceLabel":"unitOfMeasure"},{"extractedLabel":"","InvoiceLabel":"unitPrice"},{"extractedLabel":"","InvoiceLabel":"operatingUnit"},{"extractedLabel":"","InvoiceLabel":"glAccount"},{"extractedLabel":"","InvoiceLabel":"GLDate"},{"extractedLabel":"","InvoiceLabel":"extendedPrice"},{"extractedLabel":"","InvoiceLabel":"itemDescription"},{"extractedLabel":"","InvoiceLabel":"poLineNumber"},{"extractedLabel":"","InvoiceLabel":"poNumber"},{"extractedLabel":"","InvoiceLabel":"invoiceLineType"},{"extractedLabel":"","InvoiceLabel":"invoiceLineNumber"},{"extractedLabel":"","InvoiceLabel":"itemNumber"}]}', 'isBase64Encoded': False}

# handle(event,context=None)

  

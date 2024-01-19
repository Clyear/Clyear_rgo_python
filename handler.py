import json
import uuid
import utils
import boto3
import requests
from datetime import datetime
import logging


# Private lambda - doesn't return http response
def handle(event, context):
    print(event)
    invoice_data = create_invoice_data(event)
    invoice_id = invoice_data.get('invoiceId')
    
    invoice_response = None
    if invoice_id is None:
        invoice_response = create_invoice(invoice_data)
    else:
        invoice_response = update_invoice(invoice_data)
    
    if invoice_response.status_code != 200:
        errorMsg = 'Failed to create/update invoice'
        utils.notify_backend_on_failure(invoice_data.get('senderEmail'),  errorMsg, 'E0003',invoice_data.get('filepath'),invoice_data.get('receiverEmail'))
        raise ValueError(f'Unable to create/update invoice with data: {invoice_response}')

    try:
        orgId=event.get('orgId','')
        invoice_responses1 = invoice_response.json()
        invoiceId=invoice_responses1.get('invoiceId')
        invoicesource=event.get('invoiceSource','Web')
        if invoicesource=='Email':
            receiverEmail=event.get('receiverEmail',None)
            refreshData={'receiverEmail':receiverEmail,'tag':'getInvoiceList','payload':'payload','invoiceId':invoiceId}
            
        else:
            refreshData={'orgId':orgId,'tag':'getInvoiceList','payload':'payload','invoiceId':invoiceId}
        print(refreshData,'refreshData')
        fcm_response = requests.put(
        url = utils.FCM_URL,
        data = json.dumps(refreshData),
        headers = utils.API_V2_HEADER)
        print(f'fcm_response: {fcm_response}')
    except Exception as e:
        logging.exception(e)
        pass
    # Enqueue invoice to process only if it is new
    invoice_response = invoice_response.json()
    if invoice_id is None:
        enqueue_invoice(invoice_response.get('invoiceId'))

    return utils.create_200_response(invoice_response)

    
def create_invoice_data(document):
    # Default data
    DEFAULT_VALUE = ''
    DEFAULT_CURRENCY_VALUE = 'USD'
    DEFAULT_DOCUMENT_TYPE_VALUE = 'INVOICE'
    if document['status']=='Reprocessing':
        resubmitdate=str(datetime.now())
    else:
        resubmitdate=''
   
    
    # Create invoice data
    invoice_data = {
        'invoiceId': document.get('invoiceId', None),
        'senderEmail': document.get('senderEmail'),
        'receiverEmail': document.get('receiverEmail'),
        'filepath': document.get('filepath'),
        'emailContentFilePath': document.get('messageBody'),
        'analysisJobId': document.get('analysisJobId'),
        'textractFailed': document.get('textractFailed'),
        'status': document.get('status', 'Initializing'),
        'action': document.get('action', 'Insert'),
        'uploadBy': document.get('uploadBy', 'Vendor'),
        'source': document.get('invoiceSource', 'App'),
        'reSubmitedDate':resubmitdate,
        'invConfidenceLevel':0.0,
        
        'invoiceNumber': DEFAULT_VALUE,
        'dueDate': DEFAULT_VALUE,
        'invoiceAmount': '',
        'dueAmount': '',
        'orderNumber': DEFAULT_VALUE,
        'invoiceDate': DEFAULT_VALUE,
        'taxTotal': 0,
        'invoiceCurrency': '',
        'documentType': DEFAULT_DOCUMENT_TYPE_VALUE,
        'name': document.get('vendorName', DEFAULT_VALUE),
        
        'textractJson': DEFAULT_VALUE,
        'formValuesJson': DEFAULT_VALUE,
        'manualExtractFailed': False,
        'extractEngineFailed': False,
        'success': False,
        'isSuccess': True   # storing exceptions in backend
    }
    return invoice_data


# Creates new invoice with document analysis job id
def create_invoice(invoice_data):
    # Create invoice
    print(f'Creating new invoice record: {invoice_data}')
    invoice_response = requests.post(
        url = utils.SAVE_INVOICE_URL,
        data = json.dumps(invoice_data),
        headers = utils.API_V2_HEADER)
    print(f'Create invoice response: {invoice_response}')
    return invoice_response


# Updates existing invoice with new document analysis job id
def update_invoice(invoice_data):
    # Update invoice
    print(f'Updating existing invoice id: {invoice_data}')
    invoice_response = requests.put(
        url = utils.UPDATE_INVOICE_URL,
        data = json.dumps(invoice_data),
        headers = utils.API_V2_HEADER)
    print(f'Update invoice response: {invoice_response}')
    return invoice_response


# Sends invoice message to SQS
def enqueue_invoice(invoice_id):
    lambda_client = boto3.client('lambda')
    analysis_response = lambda_client.invoke_async(
        FunctionName='invoice-enqueue-process-handler',
        InvokeArgs=json.dumps({
            'invoiceId': invoice_id,
            'userId': 'invoice-message'
        })
    )
    print(analysis_response)
    print(f'Sent invoice {invoice_id} to round-robin-invoice-queue.fifo')
    return None
import json
import utils
import requests
import logging

# Private lambda - doesn't return http response
def handle(event, context):
    invoice_data = create_invoice_data(event)
    invoice_id = invoice_data.get('invoiceId')
    
    invoice_response = None
    if invoice_id is None:
        invoice_response = create_invoice(invoice_data)
    else:
        invoice_response = update_invoice(invoice_data)
    
    if invoice_response.status_code != 200:
        errorMsg = 'Failed to create/update invoice'
        utils.notify_backend_on_failure(invoice_data.get('senderEmail'), errorMsg, 'E0003',invoice_data.get('filepath'),invoice_data.get('receiverEmail'))
        raise ValueError(f'Unable to create/update invoice with data: {invoice_response}')

    return invoice_response.json()


def create_invoice_data(document):
    # Default data
    DEFAULT_VALUE = 'N/A'
    DEFAULT_CURRENCY_VALUE = 'USD'
    DEFAULT_DOCUMENT_TYPE_VALUE = 'INVOICE'
    try:
        if document['status']=='Reprocessing':
            invoice_ids=document.get('invoiceId', None)
            expense_removel_reponse = requests.delete(
            url = f'{utils.DELETE_EXPENSE_URL}{invoice_ids}',
            headers = utils.API_V2_HEADER)
            print(expense_removel_reponse,'expense_removel_reponse')
    except Exception as e:
        logging.error(e)
    
    # Create invoice data
    invoice_data = {
        'invoiceId': document.get('invoiceId', None),
        'senderEmail': document.get('senderEmail'),
        'receiverEmail': document.get('receiverEmail'),
        'filePath': document.get('filePath'),
        
        'analysisJobId': document.get('analysisJobId'),
        'textractFailed': document.get('textractFailed'),
        'status': document.get('status', 'Initializing'),
        'action': document.get('action', 'Insert'),
        'uploadBy': document.get('uploadBy', 'vendor'),
        
        'invoiceNumber': DEFAULT_VALUE,
        'dueDate': DEFAULT_VALUE,
        'invoiceAmount': '',
        'dueAmount': '',
        'orderNumber': DEFAULT_VALUE,
        'invoiceDate': DEFAULT_VALUE,
        'taxTotal': 0,
        'invoiceCurrency': "",
        'documentType': DEFAULT_DOCUMENT_TYPE_VALUE,
        'name': '',
        
        'textractJson': DEFAULT_VALUE,
        'formValuesJson': DEFAULT_VALUE,
        'manualExtractFailed': False,
        'extractEngineFailed': False,
        'success': False,
        'isSuccess': True   # storing exceptions in backend
    }
    try:
        invoice_data['emailContentFilePath']=document.get('emailContentFilePath')
        
    except :
        
        invoice_data['emailContentFilePath']='No data available'
        
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

import json
import utils
import logging
import requests

def handle(event, context):
    invoice_id = event.get('invoiceId')
    detected_entities = event.get('detectedEntities')
    create_invoice_labels(invoice_id, detected_entities)
    
def create_invoice_labels(invoice_id, detected_entities):
    invoice_labels = []
    for entity_name, entity in detected_entities.items():
        invoice_labels.append({
            'labelType': entity_name,
            'label': entity.get('label'),
            'detectedLabel': entity.get('label')
        })
    
    save_request = {
        'invoiceId': invoice_id,
        'invoiceLabels': invoice_labels
    }
    print(f'Saving new invoice labels with {save_request}')
    save_response_http = requests.post(
        f'{utils.SAVE_INVOICE_LABEL_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(save_request)
    )
    print(save_response_http)
    
    if save_response_http.status_code != 200:
        raise ValueError('An exception occurred while creating new invoice labels')
        
    print(save_response_http.content)


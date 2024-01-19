import json
import utils
import requests

def handle(event):
    save_request = {
        'invoiceId': event.get('invoiceId'),
        'invoiceLabels':event.get('invoiceLabels')
    }
    print(f'Saving invoice labels with {save_request}')
    
    save_response_http = requests.post(
        f'{utils.SAVE_EXTRACTED_LABEL_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(save_request)
    )
    print(save_response_http)
    
    if save_response_http.status_code != 200:
        raise Exception('An exception occurred while creating new invoice labels')
        
    print(save_response_http.content)
    return None

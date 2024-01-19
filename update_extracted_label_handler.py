import json
import utils
import requests

def handle(event):
    update_request = {
        'invoiceId': event.get('invoiceId'),
        'invoiceLabels':event.get('invoiceLabels')
    }
    print(f'Updating invoice labels with {update_request}')
    
    update_response_http = requests.put(
        f'{utils.UPDATE_EXTRACTED_LABEL_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(update_request)
    )
    print(update_response_http)
    
    if update_response_http.status_code != 200:
        raise Exception('An exception occurred while updating invoice labels')
        
    print(update_response_http.content)
    return None
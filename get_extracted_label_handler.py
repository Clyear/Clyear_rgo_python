import utils
import requests

def handle(invoice_id):
    get_response_http = requests.get(
        f'{utils.GET_EXTRACTED_LABELS_URL}{invoice_id}',
        headers = utils.API_V2_HEADER)
    print(get_response_http)
    invoice_labels={}
    if get_response_http.status_code != 200:
        return invoice_labels
        
    get_response = get_response_http.json()
    get_response_status = get_response.get('status')
    if get_response_status is None or get_response_status.lower() != 'success':
        raise Exception(f'Error while getting invoice labels for invoice id: {invoice_id}')

    invoice_labels = get_response.get('data')
    return invoice_labels
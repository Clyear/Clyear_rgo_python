import time
import json
import utils
import requests

# Private lambda - doesn't return http response
def handle(invoice_id):
    print(f'Finding invoice for Invoice id: {invoice_id}')
    invoice = get_invoice(invoice_id)
    print(f'Invoice detail found matching job id {invoice_id}: {invoice}')
    return invoice
    
    
def get_invoice(invoice_id):
    get_response_http = requests.get(
        url = f'{utils.GET_INVOICE_URL}{invoice_id}',
        headers = utils.API_V2_HEADER)
    print(get_response_http)

    get_invoice_response = get_response_http.json()
    get_invoice_status = get_invoice_response.get('status')
    return get_invoice_response.get('data')

import json
import utils
import requests

def handle(save_request, create_mode):
    return save_supplier(save_request, create_mode)
    
def save_supplier(save_request, create_mode):
    if create_mode:
        print('Creating new supplier name mapping record')
        save_response_http = requests.post(
            url = f'{utils.SAVE_VENDOR_URL}',
            data = json.dumps(save_request),
            headers = utils.API_V2_HEADER
        )
    else:
        print('Updating existing supplier name mapping record')
        save_response_http = requests.put(
            url = f'{utils.UPDATE_VENDOR_URL}',
            data = json.dumps(save_request),
            headers = utils.API_V2_HEADER
        )

    print(save_response_http)
    if save_response_http.status_code != 200:
        # print(f'Something went wrong while looking up supplier with email {supplier_email}')
        return None
        
    print(save_response_http.content)
    return save_response_http.content
    
    
    
import utils
import requests

def handle(event):
    customer_id = event.get('customerId')
    print(f'Finding vendor list for customer {customer_id}')

    vendor_list = get_vendor_list(customer_id)
    print('vendor_list',vendor_list)
    if vendor_list==[{}, {}, {}, {}]:
        vendor_name_list=None
        return None
        
    vendor_name_list = [vendor['vendorName'] for vendor in vendor_list]
    vendor_name_list = [name for name in vendor_name_list if name.strip() != '']
    print(f'vendor name list found: {vendor_name_list}')
    
    return vendor_name_list

# Get list of vendor for the subscriber
def get_vendor_list(customer_id):
    get_response_http = requests.get(
        url=f'{utils.GET_VENDOR_LIST_URL}{customer_id}',
        headers = utils.API_V2_HEADER)
    print(get_response_http)
    
    if get_response_http.status_code == 403:
        return []

    if get_response_http.status_code != 200:
        return []
        print(f'Unable to get vendor list for subscriber {customer_id}')
            # raise Exception(f'Unable to get vendor list for subscriber {customer_id}')
        
    get_response = get_response_http.json()
    get_response_status = get_response.get('status')
    if get_response_status != 'Success':
        raise ValueError(f'Unable to get vendor list for subscriber {customer_id}')

    return get_response.get('data')

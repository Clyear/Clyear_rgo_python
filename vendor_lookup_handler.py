import json
import utils
import requests

def handle(event):
    # Find lookup url for the subsriber
    customer_id = event.get('customerId')
    print(f'Finding LOOKUP ERP url for subscriber {customer_id}')
    lookup_service_url = get_customer_lookup_url(customer_id)
    print(f'LOOKUP ERP service url found {lookup_service_url}')
    
    if lookup_service_url is None:
        print('No LOOKUP ERP service url found')
        return None
    
    # Find vendor name for the PO Number
    po_number = event.get('poNumber')
    print(f'Finding vendor name for the PO Number {po_number}')
    vendor_name = lookup_vendor(lookup_service_url, po_number)
    print(f'vendor name found is {vendor_name}')
    
    return vendor_name

def lookup_vendor(lookup_service_url, po_number):
    lookup_request = {
        'data': [
            {
                'PONumber': po_number
            }
        ]
    }
    lookup_response_http = requests.post(
        url = lookup_service_url,
        data = json.dumps(lookup_request),
        auth = utils.OIS_BASIC_AUTH,
        headers = {
            'Content-Type': 'application/json'
        }
    )
    print(lookup_response_http)
    
    if lookup_response_http.status_code == 404:
        print(f'PO Number {po_number} not found')
        return None
        
    if lookup_response_http.status_code != 200:
        print(f'Something went wrong while looking up vendor with PO Number {po_number}')
        return None
        
    lookup_response = lookup_response_http.json()
    vendor_record = lookup_response.get('data', [None])[0]
    
    if vendor_record is not None:
        return vendor_record.get('vendor')
    
    return None

# Get all ERP urls configured for the subscriber
def get_customer_lookup_url(customer_id):
    get_response_http = requests.get(
        url=f'{utils.GET_CUSTOMER_ERP_URL}{customer_id}',
        headers = utils.API_V2_HEADER)
    print(get_response_http)
    
    if get_response_http.status_code == 403:
        return None

    if get_response_http.status_code != 200:
        raise ValueError(f'Unable to get vendor ERP details for subscriber {customer_id}')
        
    get_response = get_response_http.json()
    get_response_status = get_response.get('status')
    if get_response_status != 'Success':
        raise ValueError(f'Unable to get vendor ERP details for subscriber {customer_id}')

    erp_url_list = get_response.get('data')
    print(f'Found {len(erp_url_list)} ERP URLs for the subscriber {customer_id}')
    for erp_url in erp_url_list:
        if erp_url.get('serviceType') == utils.CUSTOMER_LOOKUP_SERVICE_TYPE:
            return erp_url.get('serviceUrl')

    return None

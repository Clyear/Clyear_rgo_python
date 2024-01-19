import utils
import requests

def handle(supplier_email, subscriber_email):
    print(f'Looking up supplier name')
    return lookup_supplier(supplier_email, subscriber_email)
    
def lookup_supplier(supplier_email, subscriber_email):
    lookup_response_http = requests.get(
        url = f'{utils.FIND_VENDOR_URL}',
        params = {
            'supplierEmail': supplier_email,
            'subscriberEmail': subscriber_email
        },
        headers = utils.API_V2_HEADER
    )
    print(lookup_response_http)
    
    if lookup_response_http.status_code == 403:
        print(f'Supplier email {supplier_email} not found')
        return None
        
    if lookup_response_http.status_code != 200:
        print(f'Something went wrong while looking up supplier with email {supplier_email}')
        return None
        
    lookup_response = lookup_response_http.json()
    supplier_record = lookup_response.get('data')
    
    if supplier_record is not None:
        supplier_name = supplier_record.get('supplierName')
        print(f'Supplier name found for {supplier_email} is {supplier_name}')
        return supplier_name
    
    print(f'Supplier record not found for {supplier_email}')
    return None
    
    
    
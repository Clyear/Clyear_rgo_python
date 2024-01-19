import json
import utils
import requests
from urllib.parse import quote

def handle(supplier_name,team_ID):
    supplier_name=quote(supplier_name)
    response_http = requests.get(
    url=f'{utils.GET_ENTITY_DATASET_URL}?vendorName={supplier_name}&orgId={team_ID}',
        headers=utils.API_V2_HEADER)
    print(response_http)
    print(response_http.url)
    
    if response_http.status_code == 403:
        print(f'No entity dataset found for the supplier: {supplier_name}')
        return {}
        
    if response_http.status_code != 200:
        raise Exception('Unable to fetch entity dataset')

    response_body = response_http.json()
    if response_body.get('status') != 'Success':
        raise Exception('Unable to fetch entity dataset')

    entity_dataset = response_body.get('data')
    if entity_dataset ==None:
        return {'invoiceLabel':None}
    print(entity_dataset,'entity_dataset')
    entity_dataset_dict = dict((entity.get('invoiceLabel'), entity) for entity in entity_dataset)
    print(f'Entity dataset dictionary fetched for the supplier {entity_dataset_dict}')
        
    return entity_dataset_dict
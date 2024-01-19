import json
import utils
import requests

def handle(event):
    # Creates new entity dataset records
    new_entity_dataset = event.get('newEntityDataset')
    if len(new_entity_dataset) == 0:
        print('No new entity dataset found to be created')
    else:
        print(f'Creating new entity dataset: {new_entity_dataset}')
        create_entity_dataset(new_entity_dataset)
    
    # Updates existing entity dataset records
    existing_entity_dataset = event.get('existingEntityDataset')
    if len(existing_entity_dataset) == 0:
        print('No entity dataset found to be updated')
    else:
        print(f'Updating entity dataset: {existing_entity_dataset}')
        update_entity_dataset(existing_entity_dataset)


def create_entity_dataset(entity_dataset):
    create_request = {
        'entityDatasetDetails': entity_dataset
    }
    print(create_request,'cp')
    create_response_http = requests.post(
        f'{utils.CREATE_DATASET_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(create_request)
    )
    print(create_response_http)
    
    if create_response_http.status_code != 200:
        raise ValueError('An exception occurred while creating new dataset')
        
    print(create_response_http.content)
    return None

    
def update_entity_dataset(entity_dataset):
    # for entity in entity_dataset:
    #     print(entity)
    update_request = {
        'entityDatasetDetails': entity_dataset
    }
    print('up',update_request)
    
    update_response_http = requests.post(
        f'{utils.CREATE_DATASET_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(update_request)
    )
    print(update_response_http)
    
    if update_response_http.status_code != 200:
        raise ValueError('An exception occurred while updating existing dataset')
        
    print(update_response_http.content)
    return None
import json
import utils
import requests

import get_entity_dataset_handler
import get_invoice_handler
import save_entity_dataset_handler
import vendor_lookup_handler
import save_vendor_handler

def handle(event, context):
    try:
        print(event)
        request_method = event.get('requestContext', {}).get('http', {}).get('method')
        if request_method == 'OPTIONS':
            return
        
        request_event = json.loads(event.get('body'))
        invoice_id = request_event.get('invoiceId')
        vendor_name = request_event.get('vendorName')
        team_ID = request_event.get('orgId')
        print(team_ID,'team_ID')
        user_entity_dataset = request_event.get('entityDataset')
        
        print('user_entity_dataset',user_entity_dataset)
        
        # Find new labels (if changed or added by user) and add it to dataset
        save_new_entity_dataset(vendor_name, user_entity_dataset,team_ID)
            
    except:
        return {
        'body': json.dumps({
            'success': True
        }),
        'statusCode': 200
        }

        
    
    # Create/Update supplier name mapping with sender/receiver email
    # save_vendor_name_mapping(invoice_id, vendor_name)
    
    return {
        'body': json.dumps({
            'success': True
        }),
        'statusCode': 200
    }

# Find new labels (if changed or added by user) and add it to dataset
def save_new_entity_dataset(vendor_name, user_entity_dataset,team_ID):
    db_entity_dataset = get_entity_dataset_handler.handle(vendor_name,team_ID)
    print(db_entity_dataset,'db_entity_dataset')

    new_entity_dataset = []
    existing_entity_dataset = []
    for user_entity in user_entity_dataset:
        target_variable = user_entity.get('invoiceLabel')
        user_field_name = user_entity.get('extractedLabel')
        # print()
        if user_field_name in utils.STANDARD_FIELD_NAME:
            print(user_field_name,'standard fieldname')
            continue
        else:
        # db_entity_fieldname=db_entity_dataset.get(user_field_name)
            db_entity = db_entity_dataset.get(target_variable,None)
            # print('db_entity',db_entity)
            # print('db_entity_fieldname',db_entity_fieldname)
            print(db_entity)
            if db_entity is None:
                newentitydict={
                
                
                }
                newentitydict['extractedLabel']=user_field_name
                newentitydict['invoiceLabel']=target_variable
                newentitydict['orgId'] = team_ID
                newentitydict['vendorName'] = vendor_name
                newentitydict['datasetType'] = 'Invoice Expenses' if target_variable in utils.LINE_ITEM_ENTITIES else 'Invoice'
                new_entity_dataset.append(newentitydict)
                print('target_variable',target_variable)
                # mylist=[]
            else:
                # print(db_entity,'db_entity')
                print(db_entity['entityTrainingDatasetId'])
                print(db_entity['extractedLabel'])
                if user_field_name != db_entity['extractedLabel']:
                    # print(db_entity.get('entityTrainingDatasetId'))
                    user_entity = {
                        'entityTrainingDatasetId':db_entity['entityTrainingDatasetId'],
                        'vendorName': vendor_name,
                        'invoiceLabel': target_variable,
                        'orgId':team_ID,
                        
                        'extractedLabel': user_field_name,
                    }
                    user_entity['datasetType'] = 'Invoice Expenses' if target_variable in utils.LINE_ITEM_ENTITIES else 'Invoice'
                    existing_entity_dataset.append(user_entity)


    save_entity_dataset_handler.handle({
        'newEntityDataset': new_entity_dataset,
        'existingEntityDataset': existing_entity_dataset
    })

# Create/Update supplier name mapping with sender/receiver email
def save_vendor_name_mapping(invoice_id, vendor_name):
    invoice = get_invoice_handler.handle(invoice_id)
    supplier_email = invoice.get('senderEmail')
    subscriber_email = invoice.get('receiverEmail')
    lookup_supplier_name = vendor_lookup_handler.handle(supplier_email, subscriber_email)
    
    save_request = {
        'supplierEmail': supplier_email,
        'subscriberEmail': subscriber_email,
        'vendorName': vendor_name
    }
    if lookup_supplier_name is None:
        save_vendor_handler.handle(save_request, True)
    else:
        save_vendor_handler.handle(save_request, False)

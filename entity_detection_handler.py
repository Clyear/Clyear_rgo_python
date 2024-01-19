import json
import boto3
import utils
import logging
import requests
import get_invoice_handler
import time
from urllib.parse import quote
# Private lambda - doesn't return http response
def handle(event):
    # print(event)
    invoiceid=event.get('invoiceId')
    vendor_name = event.get('name')
    table_data_path = event.get('tableDataPath')
    invoicedata_expense=get_invoice_handler.get_invoiceby(invoiceid)
    # print('invoicedata_expense',invoicedata_expense)
    organizationID_expense=invoicedata_expense.get('orgId')
    
    
    if table_data_path is None or table_data_path == "":
        logging.error('Table data path not found')
        raise ValueError('Table data path not found')

    detected_entities = None
    try:
        table_data = read_table_data(table_data_path)
        table_entities = detect_table_entities(table_data, vendor_name,organizationID_expense,table_data_path)
        try:
            table_entities=table_entities.get('getfirst_step2')
            return table_entities
        except:
            expense_item_table = detect_expense_item_table(table_entities)
            
            store_table_values(expense_item_table, table_data_path)
        
    except Exception as error:
        logging.error(str(error))
        raise ValueError(error)

    return expense_item_table
    
def read_table_data(table_data_path):
    # Get S3 object handle
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    table_data_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = table_data_path
    )
    
    # Read table data from S3
    table_data_str = table_data_s3_response.get('Body').read()
    table_data = json.loads(table_data_str)
    return table_data.get('tableData')

def detect_table_entities(table_data_list, vendor_name,organizationID_expense,table_data_path):
    logging.info('Detecting entities from the table data..')
    
    logger = logging.getLogger()
 
    if vendor_name=='':
        
        organizationID_expense=''

    key_list=[]
    datasetlist=[]
    table_meta_list = []
    tabledata=[]
    static_engine_entities={}
    lengthOfdatalist=len(table_data_list)
    countinglendataset=0
    print(lengthOfdatalist,'lengthOfdatalist')
    if lengthOfdatalist!=1:
    
        for table_data in table_data_list:
    
            valuejson=list(table_data[0].keys())
            print(valuejson,'valuejson')
      
        
                
    
        
            params = {
                'vendorName': vendor_name,
                'datasetType': 'Invoice Expenses',
                
                'orgId':organizationID_expense
            }
            phraseList=valuejson
            print(params,'params')
            response = requests.get(
            url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
            headers=utils.API_V2_HEADER,
            params=params)
            
            if response.status_code==403:
                params = {
                'vendorName': "",
                'datasetType': 'Invoice Expenses',
                
                'orgId':""
                }
                print(params,'params')
                response = requests.get(
                url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
                headers=utils.API_V2_HEADER,
                params=params)
            
                if response.status_code!=200 and lengthOfdatalist<=1:
                    return {}

            payload_data=response.json()
            payload_data['phraseList']=phraseList
            # print(response.elapsed.total_seconds())
            
            # print(json.dumps(payload_data))
                
            
        
            detected_entities_response = requests.post(
            url = utils.DETECT_ENTITIES_URL,
            data = json.dumps(payload_data)
            
            )
            print(detected_entities_response,'detected_entities_response')
            
            if detected_entities_response.status_code!=200 or detected_entities_response.json()=={}:
                params = {
                'vendorName': "",
                'datasetType': 'Invoice Expenses',
                
                'orgId':""
                }
                response = requests.get(
                url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
                headers=utils.API_V2_HEADER,
                params=params)
                print(params,'params')
            
            

                payload_data=response.json()
                payload_data['phraseList']=phraseList
                # print(response.elapsed.total_seconds())
                
                # print(json.dumps(payload_data))
                    
                
            
                detected_entities_response = requests.post(
                url = utils.DETECT_ENTITIES_URL,
                data = json.dumps(payload_data)
                
                )
              

            detected_entities = detected_entities_response.json()
            
            datasetlist.append(detected_entities)

        print(datasetlist,'datasetlist')
            
        
        # if is_supplier_present(vendor_name) and detected_entities == {}:
           
        #     return detect_table_entities(table_data_list, '','',table_data_path)
        # print(len(datasetlist),'length')
        
        LINE_ITEM_ENTITIES = [
        'poNumber',
        'poLineNumber',
        'itemNumber',
        'itemDescription',
        'unitOfMeasure',
        'quantity',
        'unitPrice',
        'extendedPrice',
        'taxAmount',
        'taxRate']
        

        newheaderobj={}
        getfirst_step2={}
        newheaderobjlist=[]
        for i in range (0,len(datasetlist)):
            dataobj=datasetlist[i]
            for k1,v1 in dataobj.items():
                if k1 in LINE_ITEM_ENTITIES and k1 not in newheaderobj:
                    newheaderobj[k1]={'invoiceLabel':v1,'originalLabel':v1}
                    getfirst_step2[k1]={'label':v1}
                    newheaderobjlist.append(v1)


        print('newheaderobj',newheaderobj)



   
       
        newlist=[]
        for l in datasetlist:
            new={}
            for k,v in l.items():
                
                new[k]={'invoiceLabel':v,'originalLabel':v}
                
            newlist.append(new)
            
        print(newlist,'newlist')   


        newlist2=[]
        for new in newlist:
            new2={}
            for k2,v2 in new.items():
                if k2 in newheaderobj:
                    # print(newheaderobj[k2]['invoiceLabel'])
                    new2[k2]={'invoiceLabel':newheaderobj[k2]['invoiceLabel'],'originalLabel':v2['originalLabel']}

            newlist2.append(new2)


        print(newlist2,'newlist')


        table_meta_list.append({
        'tableData': table_data_list,
        'detectedEntities': newlist2
        
        })
        newobjectlist=[]
        for i in table_meta_list:
            primarykeyvaluepair=i['tableData']
            keyvalues=i['detectedEntities']

        for km in primarykeyvaluepair:
            for mn in km :
                    # # print(mn)
                    newobjectlist.append(mn)

        print('newobjectlist',newobjectlist)
        newset=[]
        finallist=[]
        for keyva in keyvalues:
            # # print(keyva)
            for entity, value in keyva.items():
                if value not in newset:
                    newset.append(value)
        for newobj in newobjectlist:
        # # print(newobj,'newobj')
            mynewbj={}
            for v,c in newobj.items():
                # # print(v,c)
                for nnn in newset:
                    if nnn['originalLabel']==v:
                        mynewbj[nnn['invoiceLabel']]=c
                        
            finallist.append(mynewbj)

        print('finallist',finallist)
        # expenseKeyData=list(finallist[0].keys())
        # expenseKeyData.append('')
        print('getfirst_step2',getfirst_step2)
        print(newheaderobjlist)
        
        # expenseKeyData=list(finallist[0].keys())
        # # expenseKeyData.append('')
        newfn={'expenseData':finallist,'expenseKeyData':newheaderobjlist}
        print(newfn)
        s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        s3_client.put_object(
            Body = json.dumps(
                newfn,
                indent = 4,
                sort_keys = True
            ),
            Bucket = utils.BUCKET_NAME,
            Key = table_data_path
        )
        print(table_data_path,'table_data_path')
        return {'getfirst_step2':getfirst_step2}
        
        
        
    

    
    
    else:
        
        for table_data in table_data_list:
            print(table_data,'table_data')
        tabledata=tabledata+table_data
        valuejson=list(table_data[0].keys())
        if valuejson is not None or valuejson== '':
            key_list=key_list+valuejson
            
        removing_duplicate=set(key_list)
        updatekeyset=list(removing_duplicate)
        

        params = {
            'vendorName': vendor_name,
            'datasetType': 'Invoice Expenses',
            
            'orgId':organizationID_expense
        }
        
        phraseList=updatekeyset
        response = requests.get(
        url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
        headers=utils.API_V2_HEADER,
        params=params)
        
        params_for_static = {
            'vendorName': "",
            'datasetType': 'Invoice Expenses',
            
            'orgId':""
        }
        response_for_static = requests.get(
        url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
        headers=utils.API_V2_HEADER,
        params=params_for_static)
        payload_data_for_static=response_for_static.json()
        payload_data_for_static['phraseList']=phraseList
        # print(response_for_static.elapsed.total_seconds())
        
        print(json.dumps(payload_data_for_static),'staticdata')
        detected_entities_response_static = requests.post(
        url = utils.DETECT_ENTITIES_URL,
        data = json.dumps(payload_data_for_static)
        
        )
        print(detected_entities_response_static)
        if detected_entities_response_static.status_code==200:
            static_engine_entities=detected_entities_response_static.json()
            
        
        if response.status_code==403:
            params = {
            'vendorName': "",
            'datasetType': 'Invoice Expenses',
            
            'orgId':""
            }
            response = requests.get(
            url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
            headers=utils.API_V2_HEADER,
            params=params)
            
            
            
        if response.status_code!=200:
            return {}

        payload_data=response.json()
        payload_data['phraseList']=phraseList
        print(response.elapsed.total_seconds())
        
        print(payload_data)
        
        detected_entities_response = requests.post(
        url = utils.DETECT_ENTITIES_URL,
        data = json.dumps(payload_data)
        
        )
        print(detected_entities_response)
        if detected_entities_response.status_code!=200 or detected_entities_response.json()=={}:
            params = {
            'vendorName': "",
            'datasetType': 'Invoice Expenses',
            
            'orgId':""
            }
            response = requests.get(
            url=f'{utils.NODE_EXTRACTION_URL}/invoice/getTrainingDataset',
            headers=utils.API_V2_HEADER,
            params=params)
        
        

            payload_data=response.json()
            payload_data['phraseList']=phraseList
            # print(response.elapsed.total_seconds())
            
            # print(json.dumps(payload_data))
                
            
        
            detected_entities_response = requests.post(
            url = utils.DETECT_ENTITIES_URL,
            data = json.dumps(payload_data)
            
            )
              
        
        

        if detected_entities_response.status_code == 500:
            return{}
        
    

        if detected_entities_response.status_code != 200 :
            print('Unable to predict invoice entities from the table')
            return {}
            # raise ValueError('Unable to predict invoice entities from the table')

        detected_entities = detected_entities_response.json()
        print(detected_entities,'detect',static_engine_entities,'static')
        detected_entities=getmergeentity(static_engine_entities,detected_entities)
        
        # if is_supplier_present(vendor_name) and detected_entities == {}:
        #     print(f'No detected entities found for the supplier {vendor_name}')
        #     print('Re-running with static extraction engine')
        #     # organizationID_expense=''
        #     return detect_table_entities(table_data_list, '','')
        
        entity_label_dict = {}
        for entity_name, label in detected_entities.items():
            entity_label_dict[entity_name] = {
                'label': label
            }
        # updatekeyset.append('')
        table_meta_list.append({
            'tableData': tabledata,
            'detectedEntities': entity_label_dict,
            'tableKeys':updatekeyset
        })
        return table_meta_list
def detect_expense_item_table(table_meta_list):
    max_columns = 0
    detected_expense_item_table = {}
    for table_meta in table_meta_list:
        data = table_meta.get('data')
        detectedEntities = table_meta.get('detectedEntities')
        
        # no_of_detected_columns = len(detectedEntities)
        # if no_of_detected_columns > max_columns:
        #     max_columns = no_of_detected_columns
        detected_expense_item_table = table_meta
    # print('detected_expense_item_table',detected_expense_item_table)      
    return detected_expense_item_table

# Store form values as json in S3
def store_table_values(expense_item_table, table_values_file_path):
    # print('table_values_file_path',table_values_file_path)
    table_data={}
    print(expense_item_table,'expense_item_table')
    table_values = expense_item_table.get('tableData')
    table_data['expenseData']=table_values
    table_data['expenseKeyData']=expense_item_table.get('tableKeys')
    if table_data == {} or table_data is None:
        return 
    
    else:
        print('table_data23',table_data)
        
        s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        s3_client.put_object(
            Body = json.dumps(
                table_data,
                indent = 4,
                sort_keys = True
            ),
            Bucket = utils.BUCKET_NAME,
            Key = table_values_file_path
        )
        
    return table_values_file_path    
    
def is_supplier_present(vendor_name):
    if vendor_name is None or vendor_name == "" or vendor_name == utils.DEFAULT_VENDOR_NAME:
        return False
    return True

# def getmergeentity(static_entity,dynamic_entity):
#     INVOICE_ENTIITES = LINE_ITEM_ENTITIES = [
#     'operatingUnit',
#     'invoiceExpenseType',
#     'invoiceLineNumber',
#     'poNumber',
#     'poLineNumber',
#     'itemNumber',
#     'itemDescription',
#     'unitOfMeasure',
#     'quantity',
#     'unitPrice',
#     'extendedPrice',
#     'GLDate',
#     'glAccount',
#     'taxAmount',
#     'taxRate',
#     'PRODUCT_CODE',
#     'ITEM',
#     'PRICE',
#     'QUANTITY',
#     'UNIT_PRICE',
#     'EXPENSE_ROW',
#     'OTHERS'
#     ]

#     new_item={}

#     for i in INVOICE_ENTIITES:
        
#         if i in dynamic_entity:
#             print(i,'1')
#             new_item[i]=dynamic_entity[i]
#         elif i in static_entity:
#             print(i,'2')
#             new_item[i]=static_entity[i]
            
            
#     print(new_item,'lineitem')
#     return new_item

def getmergeentity(static_entity,dynamic_entity):
    INVOICE_ENTIITES = LINE_ITEM_ENTITIES = [
    'operatingUnit',
    'invoiceExpenseType',
    'invoiceLineNumber',
    'poNumber',
    'poLineNumber',
    'itemNumber',
    'itemDescription',
    'unitOfMeasure',
    'quantity',
    'unitPrice',
    'extendedPrice',
    'GLDate',
    'glAccount',
    'taxAmount',
    'taxRate',
    'PRODUCT_CODE',
    'ITEM',
    'PRICE',
    'QUANTITY',
    'UNIT_PRICE',
    'EXPENSE_ROW',
    'OTHERS'
    ]

    new_item={}

    for i in INVOICE_ENTIITES:
        if i in dynamic_entity:
            print(i,'1dynamic')
            new_item[i]=dynamic_entity[i]
        elif i in static_entity:
            foundmatch=False
            print(i,'i2static')
            for o,p in dynamic_entity.items():
                
                
                checkdata=static_entity[i]
                
                if p == checkdata:
                    print(p,'2dynamic value')
                    foundmatch=True
                    break
                    
                # else:
                #     foundmatch=False
                    
                 
                    
            if not foundmatch:
                new_item[i]=static_entity[i]
            
            
    print(new_item,'lineitem')              
    return new_item

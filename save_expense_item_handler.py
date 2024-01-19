import re
import json
import utils
import requests
import boto3
import logging

def handle(event):
    # print(event,'checkeven')
    detected_entities = event.get('detectedEntities')
    print(event,'event save')
    filepath = event.get('filePath')
    tablevalue=event.get('tableDataPath')
    
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
    Bucket = utils.BUCKET_NAME,
    Key = tablevalue
    )

    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)
    print(document_json_list)
    
    entity_label_map = get_entity_label_map(detected_entities)

    table_data = document_json_list.get('expenseData')
    expense_item_data = get_expense_item_data(table_data, entity_label_map)

    filepath = event.get('filePath')

    try:
        slicingdata(event)
        
    except:
        pass
    save_expense_item(filepath, expense_item_data,event)
    

def get_entity_label_map(detected_entities):
    entity_label_map = {}
    for entity, value in detected_entities.items():
        
        label = value.get('Label',None)
        if not label:
            label = value.get('label',None)
            
        entity_label_map[label] = entity
    return entity_label_map
    
def get_expense_item_data(table_data, entity_label_map):
    expense_item_data = []
    print('table_datachck1',table_data)
    # print()
    for row in table_data:
        record = {}
        for label, value in row.items():
            if label=='':
                continue
            else:
                
                entity = entity_label_map.get(label)
                if entity is not None:
                    set_entity_value(record, entity, value)
                    
        expense_item_data.append(record)
    return expense_item_data

def set_entity_value(record, entity, value):
   
    if entity == 'extendedPrice' or  entity=='taxRate':
        try:
            match = re.findall('[\d,]+[\.]?\d+', value)
        
      
            
            # print(document_json_list)
            if len(match) > 0:
                response1= float(match[0].replace(',', ''))
                record[entity] = "{:.2f}".format(float(response1))
            else:
                record[entity]=value
                
        except:
            record[entity]=value
            
    elif entity=='unitPrice':
        try:
            match = re.findall('[\d,]+[\.]?\d+', value)
        
      
            
            # print(document_json_list)
            if len(match) > 0:
                response1= match[0].replace(',', '')
                checkdecimalornot=is_float_string(response1)
                if checkdecimalornot:
                    record[entity] = str(response1)
                else:
                    record[entity] = "{:.2f}".format(float(response1))

            else:
                record[entity]=value
                
        except:
            record[entity]=value    
    else:
        
        record[entity] = value

def save_expense_item(filepath, expense_item_data,event):
    print('event check',event)
    invoiceAmount=event.get('invoiceAmount',0)
    taxTotal=event.get('taxTotal',0)
    subTotal=event.get('subTotal',0)
    # if not invoiceAmount and not taxAmount :
    #     invoiceAmount=0
    #     taxTotal=0
    #     subTotal=0
        
    try:
        print(expense_item_data,'expense_item_data')
        expense_item_data1=[]
        for itemdata in expense_item_data:
            if 'taxAmount' in itemdata and 'extendedPrice' in itemdata :
                extprice=itemdata.get('extendedPrice',None)
                if extprice:
                    try:
                        if '%' in itemdata['taxAmount']:
                            taxamt=itemdata['taxAmount'].replace('%','')
                            taxamt=taxamt.replace('$','')
                            twodigittaxrate="{:.2f}".format(float(taxamt))
                            itemdata['taxRate']=str(twodigittaxrate)
                            taxAmount=((float(taxamt)*float(extprice))/100)
                            itemdata['taxAmount']=taxAmount
                            
                            print(taxamt,'taxamt')
                            
                            
                        else:
                            taxamt=itemdata['taxAmount'].replace('%','')
                            taxamt=taxamt.replace('$','')
                            
                            taxRate=((float(taxamt)/float(extprice))*100)
                            taxRate = "{:.2f}".format(float(taxRate))
                            
                            itemdata['taxRate']=str(taxRate)
                            itemdata['taxAmount']=str(taxamt)
                    except Exception as e:
                        logging.exception(e)
                        pass
                # expense_item_data1.append(itemdata)
            elif 'taxRate' in itemdata and 'taxAmount' not in itemdata and 'extendedPrice' in itemdata:
                extprice=itemdata.get('extendedPrice',None)
                try:
                    if extprice:
                        taxrateforms=itemdata['taxRate'].replace('%', '')
                        taxrateforms=taxrateforms.replace('$', '')
                        taxrateforms=taxrateforms.strip()
                        taxratewith2digit="{:.2f}".format(float(taxrateforms))
                        
                        
                        
                        taxAmount=((float(taxrateforms)*float(extprice))/100)
                        taxAmount="{:.2f}".format(float(taxAmount))
                        itemdata['taxAmount']=str(taxAmount)
                        itemdata['taxRate']=str(taxratewith2digit)
                        
                except Exception as e:
                    logging.exception(e)
                    pass
                        
                
            
            
            expense_item_data1.append(itemdata)
    except Exception as e:
        logging.exception(e)
        
        
                
                
    if not expense_item_data1:
        expense_item_data1=expense_item_data
    save_request = {
        'filepath': filepath,
        'invoiceExpenses': expense_item_data1,
        'invoiceAmount':invoiceAmount,
        'taxTotal':taxTotal,
        'subTotal':subTotal
        
        
    }
    
    print(json.dumps(save_request))
    save_response_http = requests.post(
        f'{utils.SAVE_EXPENSE_ITEM_URL}',
        headers = utils.API_V2_HEADER,
        data = json.dumps(save_request)
    )
    print(save_response_http)
    
    if save_response_http.status_code != 200:
        raise ValueError('An exception occurred while saving invoice line items')
        
    print(save_response_http.content)
    

def slicingdata(event):
    
    newlineitemlist=[]
    newlineitemlist2=[]
    
    keylist=[]
    detected_entities = event.get('detectedEntities')
    # table_data = event.get('tableData')
    filepath = event.get('filePath')
    entity_label_map = get_entity_label_map(detected_entities)
    
    tablefilepath=filepath.replace(f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/','')
    tablekey_filepath=tablefilepath+'-table-values.json'
    extension=['.jpeg','.png','.tiff','.jpg']
    
    for ext in extension:
        if ext in tablekey_filepath:
            tablekey_filepath=tablekey_filepath.replace(ext,'.pdf')
            
    
    getting_table_data = read_table_data(tablekey_filepath)
    table_data=getting_table_data.get('expenseData')
      
    for key in table_data:
        
        # print(key)
        appendict={}
        for k,v in key.items():
            
            slicing_value=key[k]
            try:
                slicing_value=slicing_value.replace("$","")
            except:
                pass
            try:
                slicing_value=slicing_value.replace('%','')
            except:
                pass
            try:
                slicing_value=slicing_value.replace(',','')
            except:
                pass
            try:
                slicing_value=slicing_value.strip()
            except:
                pass
                
            appendict[k]=slicing_value
            
        newlineitemlist.append(appendict)
    print(newlineitemlist)   
    for key1 in newlineitemlist:
        appendict1={}
        
        for k2,v2 in key1.items():
            entity1=entity_label_map.get(k2,'')
            # print(entity1)
            if  entity1=='extendedPrice':
                match = re.findall('[\d,]+[\.]?\d+', v2)
                
                if len(match) > 0:
                    ressponse=float(match[0].replace(',', '') )
                    appendict1[k2] = "{:.2f}".format(float(ressponse))
            elif entity1== 'unitPrice':
                match = re.findall('[\d,]+[\.]?\d+', v2)
                
                if len(match) > 0:
                    ressponse=match[0].replace(',', '')
                    decimalornot=is_float_string(ressponse)
                    if decimalornot:

                        appendict1[k2] = str(ressponse)
                    else:
                        appendict1[k2] = "{:.2f}".format(float(ressponse))
            elif entity1=='poLineNumber'or entity1=='invoiceLineNumber':
                appendict1[k2] = re.sub("[^0-9],*","",v2)
            else:
                appendict1[k2]=v2
                
        newlineitemlist2.append(appendict1)
    try:
        if 'taxAmount' in detected_entities and 'extendedPrice' in detected_entities:
            extendedprice=detected_entities['extendedPrice']['label']
            taxamount=detected_entities['taxAmount']['label']
            for value1 in newlineitemlist2:
                
                try:
                    taxamount1=value1[taxamount].strip()
                    extendedprice2=value1[extendedprice].strip()
                    print(taxamount1,'taxamount1',extendedprice2,'extendedprice2')
                    taxRate=str((float(taxamount1)/float(extendedprice2))*100)
                    print(taxRate,'taxRate')
                except Exception as e:
                    logging.exception (e)
                    taxRate=None
                if taxRate:
                    value1['taxRate']=taxRate
                    updatekey=getting_table_data['expenseKeyData']
                    checkcount=updatekey.count('taxRate')
                    if checkcount==0:
                        updatekey.append('taxRate')
                        updatekey.append('taxRate/labelCheck')
                    else:
                        updatekey=updatekey
                
                newlinelist.append(value1)
                        
            getting_table_data['expenseKeyData']=updatekey
                
                
        elif 'taxAmount' not in detected_entities and 'taxRate' in detected_entities and 'extendedPrice' in detected_entities :
            extendedprice=detected_entities['extendedPrice']['label']
            taxrate=detected_entities['taxRate']['label']
            for value1 in newlineitemlist2:
                
                try:
                    taxrate1=value1[taxrate].strip()
                    extendedprice2=value1[extendedprice].strip()
                    print(taxrate1,'taxrate1',extendedprice2,'extendedprice2')
                    taxAmount=str((float(taxrate1)*float(extendedprice2))/100)
                    print(taxAmount,'taxAmount')
                except Exception as e:
                    logging.exception (e)
                    taxRate=None
                if taxAmount:
                    value1['taxAmount']=taxAmount
                    updatekey=getting_table_data['expenseKeyData']
                    checkcount=updatekey.count('taxAmount')
                    if checkcount==0:
                        updatekey.append('taxAmount')
                        updatekey.append('taxAmount/labelCheck')
                        # row[label+'/labelCheck']="recommended"
                    else:
                        updatekey=updatekey
                
                newlinelist.append(value1)
                        
            getting_table_data['expenseKeyData']=updatekey
                
        else:
            newlinelist=newlineitemlist2
    except Exception as e:
        logging.exception(e)
        newlinelist=newlineitemlist2
    print(newlinelist,'newlinelist')
        
    getting_table_data['expenseData']=newlineitemlist2
    
        
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
        Body = json.dumps(
        getting_table_data,
        indent = 4,
        sort_keys = True
        ),
        Bucket = utils.BUCKET_NAME,
        Key = tablekey_filepath
    )

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
    return table_data


def is_float_string(value):
    decimal_point_count = 0
    for char in value:
        if char.isdigit():
            continue
        elif char == ".":
            decimal_point_count += 1
            if decimal_point_count > 1:
                return False
        else:
            return False
    return decimal_point_count == 1


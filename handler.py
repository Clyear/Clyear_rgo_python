import json
import utils
import traceback
import requests
import logging
import boto3
import base64

from datetime import datetime
from collections import Counter

import get_invoice_handler
import table_extraction_handler
import entity_detection_handler
import save_extracted_label_handler
import save_expense_item_handler
import standardizedextraction

# Private lambda - doesn't return http response
# Input: {expenseJobId: '', expenseJsonPath: ''}
logger = logging.getLogger()
# try: # for Python 3
#     from http.client import HTTPConnection
# except ImportError:
#     from httplib import HTTPConnection
# HTTPConnection.debuglevel = 1

# logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

# print('request',requests.get('https://httpbin.org/headers'))

def handle(event, context):
    print(f'Event from caller: {event}')
    
    try:
        # Step 1 - Get invoice by expense job id
        invoice_response = get_invoice_handler.handle(event, context)
        print(invoice_response)
        
        table_extraction_event = invoice_response.copy()
        table_extraction_event.update({
            'expenseJsonPath': event.get('expenseJsonPath')
        })
    
       # Step 2 - Table data extraction
        try:
            table_values_response = table_extraction_handler.handle(table_extraction_event, context)
            print(table_values_response)
        
            extraction_event = table_extraction_event.copy()
            extraction_event.update({
                'tableDataPath': table_values_response['tableValuesFilePath']
            })
        except Exception as err:
            logging.exception( err)
            pass

        try:
            standarizationextraction=standardizedextraction.handle(event,invoice_response)
            
        except Exception as e:
            print(e,'findingerror')

        
            
        
        # Step 3 - Detect entities based on supplier name
        try:
            
            supplier_name = invoice_response.get('name')
            table_meta_data = extraction_handler(extraction_event, supplier_name)
            # print(table_meta_data)
        
            save_expense_item_event = extraction_event.copy()
            table_meta_data_check=table_meta_data.get('tableData',None)
            if table_meta_data_check:
                save_expense_item_event.update({
                    'tableData': table_meta_data.get('tableData'),
                    'detectedEntities': table_meta_data.get('detectedEntities')
                })
            else:
                save_expense_item_event.update({
                    
                    'detectedEntities': table_meta_data
                })
                
        except Exception as err:
            logging.exception( err)
            pass
            
        
        # Step 4 - Create/Update invoice labels
        try:
            save_extracted_label_handler.handle(save_expense_item_event, context)
        except Exception as err:
            logging.exception( err)
            pass
    
        
        try:
            save_expense_item_handler.handle(save_expense_item_event)
        except Exception as err:
            logging.exception( err)
            pass
        
        
        
        print(f'Event from callerlast: {event}')
        getinvoice_data=event['expenseJobId']
        updating_invoice_data=get_invoice_handler.get_invoice(getinvoice_data)
        print('updating_invoice_data',updating_invoice_data)
        # updating_invoice_data['status']='Pending'
        print('updated invoice data',updating_invoice_data)
      
        keyfor_data=updating_invoice_data['tableValuesJson']
        keyfor_datas=keyfor_data.replace(f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/',"")
        print(keyfor_datas,'keyfor_datas')
        getfilepath=updating_invoice_data['filePath']
        slicingfilepath=getfilepath.replace(f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/','')
        extlist=['.png','.tiff','.jpg','.jpeg']
        for ext in extlist:
            if ext in slicingfilepath.lower():
                print(ext)
                slicingfilepath=slicingfilepath.replace(ext,'.pdf')
        
        get_vendorfilepath=slicingfilepath+'-textracted-table.json'
        getformvaluepath=slicingfilepath+'-textracted.json'
        
        keyfor_data1=updating_invoice_data['formValuesJson']
        keyfor_datas1=keyfor_data1.replace(f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/',"")
        print(get_vendorfilepath,get_vendorfilepath,'keyfor_datas1')
        
        try:
            s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
            document_json_s3_response1 = s3_client.get_object(
            Bucket = utils.BUCKET_NAME,
            Key = get_vendorfilepath
            )
    
            document_json_str1 = document_json_s3_response1.get('Body').read()
            document_json_list1 = json.loads(document_json_str1)
            # print(document_json_list1)
            vendor_list=[]
            vendor_adreeslist=''
            for a in document_json_list1:
                combine_document=a['ExpenseDocuments']
                
                for b in combine_document:
                    summar_document=b['SummaryFields']
                    for c in summar_document:
                        if c['Type']['Text']=='VENDOR_NAME':
                            # print(k['ValueDetection']['Text'])
                            vendor_list.append(c['ValueDetection']['Text'])
                        elif c['Type']['Text']=='VENDOR_ADDRESS':
                            # print(k['ValueDetection']['Text'])
                            vendor_adreeslist=vendor_adreeslist+(c['ValueDetection']['Text'])
                
        except Exception as e:
            logging.exception(e)
            vendor_list=''
            vendor_adreeslist=''
            
            pass
        try:
            getinvoicecurrency=updating_invoice_data['invoiceCurrency']
            if not getinvoicecurrency:
            
                currency=currencydetection(document_json_list1)
                if currency:
                    if currency=='BZR':
                        currency='BRL'
                        
                    getinvoicecurrency=currency
                    
                    updating_invoice_data['invoiceCurrency']=getinvoicecurrency
                else:
                    try:
                        togetwordlist=getwordlist(getformvaluepath)
                        for cur in utils.currencylist:
                            if cur in togetwordlist:
                                updating_invoice_data['invoiceCurrency']=cur
                                
                    except Exception as e:
                        logging.exception(e)
        except Exception as e:
            logging.exception(e)
        #     mylist=['TERMS','Terms','Term','terms',]
        #     extractdays=document_json_list['documentData']
        #     try:
        #         for key,value in extractdays.items():
        #             if any(x in key for x in mylist) and key!='Terms of delivery:' and key!='Trade Terms:':
        #                 adding_value=value
        #                 adding_key=key
        #                 workingdata=True
    
        #     except:
        #         pass
        #         # workingdata=False
            
        #     try:
        #         # date = datetime.strptime(adding_value, '%m/%d/%Y')
        #         # print("The string is a date with format " )
        #         if updating_invoice_data['dueDate']!='':
                    
        #             duedateentry=try_parsing_date(updating_invoice_data['dueDate'])
                    
                    
        #             updating_invoice_data['dueDate']=str(duedateentry)
        #     except :
        #         print("The string is not a date with format " )
        #         updating_invoice_data['dueDate']=""
            
            
        # except:
        #     pass
        
        # try:
        #     s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        #     document_json_s3_response = s3_client.get_object(
        #     Bucket = utils.BUCKET_NAME,
        #     Key = keyfor_datas
        #     )
    
        #     document_json_str = document_json_s3_response.get('Body').read()
        #     document_json_list = json.loads(document_json_str)
        #     print(document_json_list,'document_json_list00')
            
        #     getconfidencelist1=document_json_list['lineData']
        #     for confidencelist in getconfidencelist1:
                
        #         getconfidencelist=confidencelist["confidencelist"]
            
            
        #     print('getconfidencelist',getconfidencelist)
        #     getconfidence=cummulativeconfidence(getconfidencelist)
        #     extraction_cumulative=updating_invoice_data['invConfidenceLevel']
        #     totalconfidence=float(getconfidence)+float(extraction_cumulative)
        #     totalcumulative=totalconfidence/2
        #     print(totalcumulative,'totalcumulative')
        #     updating_invoice_data['invConfidenceLevel']=float(totalcumulative)
        # except:
            
        #     pass
        
        updating_invoice_data['suggestedVendorName']=json.dumps(vendor_list)
        updating_invoice_data['suggestedVendorAddress']=vendor_adreeslist
        
        print('updating_invoice_data_updating_invoice_data vendor details check',updating_invoice_data)
        
        
        # updating_invoice_data['status']='Pending Review'
        # updating_invoice_data['status']='Processing'
        
        response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
        print(response_update,'response_update final')
        try:
            autappprovalprocess= requests.put(
            url = utils.AUTO_APPROVAL,
            data = json.dumps(updating_invoice_data),
            headers = utils.API_V2_HEADER)
            print(json.dumps(updating_invoice_data),'c')
            print(autappprovalprocess.status_code,'apcheck')
            get_autappproval_response = autappprovalprocess.json()
            if autappprovalprocess.status_code == 200:
                pass
            elif autappprovalprocess.status_code != 200:
                
                updating_invoice_data['status']='Pending Review'
                
                print(updating_invoice_data,'pending reviw check')
                response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
                print(response_update,'response_update final1')
                
        #         updating_invoice_data['status']='Aut
            
        except Exception as err:
            logging.exception( err)
            
            updating_invoice_data['status']='Pending Review'
            print(updating_invoice_data,'pending reviw check')
            response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
            print(response_update,'response_update final1,except')
            pass
        
        # try:
            
        #     getinvoiceid=updating_invoice_data['invoiceId']
            
        #     touchelssinvoicedata=get_invoice_handler.GET_TOUCH_LESS(getinvoiceid)
        #     print(touchelssinvoicedata,'touchelssinvoicedata')
            
        #     autappprovalprocess= requests.post(
        #     url = utils.AUTO_APPROVAL,
        #     data = json.dumps(touchelssinvoicedata),
        #     headers = utils.API_V2_HEADER)
        #     print(autappprovalprocess.status_code)
        #     get_autappproval_response = autappprovalprocess.json()
        #     print(get_autappproval_response.get('data'))
        #     getuserid=get_autappproval_response.get('data')
        #     getuserid=getuserid['userId']
        #     print('getuserid',getuserid)
            
            
        #     if autappprovalprocess.status_code == 200:
        #         updating_invoice_data['status']='Auto Approved'
        #         tokenjson={'userId':getuserid}
        #         encryptedtocken=flutterencription(tokenjson)
                
        #         response_update_token = requests.get('https://dev-api-v3.ezcloud.dev/user/refreshToken?flutterString='+encryptedtocken+'')
        #         print(response_update_token.headers['accesstoken'])
        #         acesstoken_v3=response_update_token.headers['accesstoken']
                
        #         status_data={
        #           "userId": getuserid,
        #           "invoiceId": touchelssinvoicedata['invoiceId'],
        #           "status": "Auto Approved",
        #           "comments": "Toucless Api Approved",
        #           "isExceptionResolved": "0",
        #           "adminUrl": "https://app.ezcloud.dev/"
        #         }
        #         API_V2_HEAD ={'authorization': acesstoken_v3,
        #         'Content-Type': 'application/json'
        #         }
        #         encrypted_status=flutterencription(status_data)
        #         encryptedjson={'webString':'','flutterString':encrypted_status}
                
        #         print('encryptedjson',encryptedjson)
                
        #         response_update_invoice = requests.put('https://dev-api-v3.ezcloud.dev/invoice/updateInvoiceStatus', data = json.dumps(encryptedjson), headers = API_V2_HEAD)
                
        #         print(response_update_invoice,'response_update_invoice')
                
                
                
                
                            
                
                
                
            
            # updating_invoice_data['status']='Pending Review'
            # response_update1 = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
            # print(response_update1)
        # except:
            
        #     updating_invoice_data['status']='Pending Review'
        #     response_update1 = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
        #     print(response_update1)
            
           
        
        # duedateextraction(keyfor_datas,updating_invoice_data)
    except Exception as error:
        traceback.print_exc()
        print(error)

    return None
    
def extraction_handler(event, vendor_name):
    entities = {}
    if is_supplier_present(vendor_name) is False:
        print('Supplier name not found in invoice')
        vendor_name = utils.DEFAULT_VENDOR_NAME
        entities = static_extraction_handler(event)
    else:
        print(f'Detecting entities using Dynamic Extraction Engine for {vendor_name}')
        entities = dynamic_extraction_handler(event, vendor_name)
    return entities

# Dynamic extraction engine with supplier name must be provided
def dynamic_extraction_handler(event, vendor_name):
    event_copy = event.copy()
    event_copy['name'] = vendor_name
    detected_entities = entity_detection_handler.handle(event_copy)
    return detected_entities
    
# Static extraction engine with no supplier    
def static_extraction_handler(event):
    event_copy = event.copy()
    event_copy['name'] = ''
    detected_entities = entity_detection_handler.handle(event_copy)
    return detected_entities        
    
def is_supplier_present(vendor_name):
    if vendor_name is None or vendor_name == "" or vendor_name == utils.DEFAULT_VENDOR_NAME:
        return False
    return True
    
def cummulativeconfidence(cumlist):
    n=0
    for cummilative in cumlist:

        n=n+float(cummilative)

    print(n)

    get_cummulative=n/len(cumlist)
    

    print(get_cummulative,"get_cummulative")

    return get_cummulative
    
    
def try_parsing_date(text):
    from datetime import datetime
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y','%m/%d/%Y','%d/%m/%y','%m/%d/%Y','%m/%d/%y','%d/%m/%Y'):
        try:
            val=datetime.strptime(text, fmt)
            val2=val.strftime('%m/%d/%Y')
            print(val2,'check')
            return val2
            
        except ValueError:
            pass
    raise ValueError('no valid date format found')


    
def flutterencription(myByteString):
    myval=json.dumps(myByteString)

    myval=myval.encode('utf-8')

    salt_key=json.dumps("Ezcloud@123")
    salt_key=salt_key.encode('utf-8')

    addingslash=base64.b64encode(myval)+b'/' +base64.b64encode(salt_key)


    encrypted_value=addingslash.decode("utf-8")
    print(encrypted_value)

    return encrypted_value

def duedateextraction(keyfor_datas,updating_invoice_data):
    try:
        s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = keyfor_datas
        )

        document_json_str = document_json_s3_response.get('Body').read()
        document_json_list = json.loads(document_json_str)
        print(document_json_list)
        mylist=['TERMS','Terms','Term','terms',]
        extractdays=document_json_list['documentData']
        try:
            for key,value in extractdays.items():
                if any(x in key for x in mylist) and key!='Terms of delivery:' and key!='Trade Terms:':
                    adding_value=value
                    adding_key=key
                    workingdata=True

        except Exception as err:
            logging.exception( err)
            pass
            # workingdata=False
        
        try:
            date = datetime.strptime(adding_value, '%m/%d/%Y')
            print("The string is a date with format " )
            updating_invoice_data['dueDate']=adding_value
        except Exception as err:
            logging.exception( err)
            print("The string is not a date with format " )
            updating_invoice_data['dueDate']=""
        
        
    except Exception as err:
        logging.exception( err)
        pass
    print('updating_invoice_data_updating_invoice_data',updating_invoice_data)
    
    response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
    print(response_update)
    
    
def currencydetection(jsonstring):
    currencylist=[]
    for load in jsonstring:
        exp=load['ExpenseDocuments']
        
        for summ in exp:
            summary=summ['SummaryFields']
            
            for currency in summary:
                try:
                    currencylist.append(currency['Currency']['Code'])
                    
                except:
                    pass
                
                
    if currencylist:
        print(currencylist,'currencylist')
        try:
            counter = Counter(currencylist)
            most_common = counter.most_common(1)
            most_frequent_string = most_common[0][0]
            return most_frequent_string
        except Exception as e:
            logging.exception(e)
            return ''
        
    else:
        return ''
    
def getwordlist(getformvaluepath):
    try:
        s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = getformvaluepath
        )
        contentlist=[]

        document_json_str = document_json_s3_response.get('Body').read()
        document_json_list = json.loads(document_json_str)
        for document in document_json_list:
            block_value=document['Blocks']
        for block in block_value:
            if block['BlockType']=='WORD':
            # print(block['Text'])
                contentlist.append(block['Text'].strip())
            
        print(contentlist,'contentlist')
        # print(document_json_list)
        return contentlist

        
        
    except Exception as err:
        logging.exception( err)
        pass
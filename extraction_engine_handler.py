import json
import boto3
import utils
import logging
import requests
import re
import datetime as dat
from datetime import datetime as dattime
from dateutil import parser

import get_invoice_handler
import form_extraction_handler
import entity_detection_handler
import vendor_lookup_handler
import get_vendor_list_handler
import vendor_name_finder
import save_invoice_handler
import analyse_expense_starter
import save_invoice_label_handler
import currency_extraction


from urllib.parse import quote

# logger = logging.getLogger()
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

# Private lambda - doesn't return http response
# Input: {analysisJobId: '', documentJsonPath: ''}
def extraction_engine_handler(event, context):
    print(f'Event from caller: {event}')

    try:
        # Step 1 - Get invoice by analysis job id
        invoice_response = get_invoice_handler.handle(event, context)
        print(invoice_response)
        
        form_extraction_event = invoice_response.copy()
        form_extraction_event.update({
            'documentJsonPath': event.get('documentJsonPath')
        })

        # Step 2 - Form data extraction
        form_values_response = form_extraction_handler.handle(form_extraction_event, context)
        print('form_values_response:',form_values_response)
    
        extraction_event = form_extraction_event.copy()
        extraction_event.update({
            'documentDataPath': form_values_response['formValuesFilePath']
        })
        
        extraction_event['languageCode']=form_values_response.get('extractlanguangecode','en')
    
        # Step 3 - Detect entities based on Vendor name identification
        vendor_name, detected_entities = extraction_handler(extraction_event)

        save_invoice_event = extraction_event.copy()
        save_invoice_event.update({
            'detectedEntities': detected_entities,
            'vendorName': 'N/A' if vendor_name is None else vendor_name
        })
        
        # Step 4 - Create/Update invoice labels
        save_invoice_label_handler.handle(save_invoice_event, context)
    
        # Step 5 - Start analyse expense and update invoice with job id
        analyse_expense_response = analyse_expense_starter.handle(save_invoice_event)
        print(analyse_expense_response)
        
        save_invoice_event.update({
            'expenseJobId': analyse_expense_response.get('expenseJobId')
        })
        
        # Step 6 - Create/Update invoice
        save_invoice_response = save_invoice_handler.handle(save_invoice_event, context)
        print(save_invoice_response)
        extracting_duedate=extractingduedate(save_invoice_event)
        get_the_confidence=invoiceconfidence(event)
        
        getinvoiceid=save_invoice_event['invoiceId']
        print('getinvoiceid',getinvoiceid)
        getiing_invoicedata=get_invoice_handler.get_invoiceby(getinvoiceid)
        print('getiing_invoicedata',getiing_invoicedata)
        getiing_invoicedata['invConfidenceLevel']=float(get_the_confidence)
        
        # try:
        #     invoiceCurrency=currency_extraction.handle(save_invoice_event)
        #     if invoiceCurrency:
        #         getiing_invoicedata['invoiceCurrency']=invoiceCurrency
                
            
        # except Exception as e:
        #     logging.exception(e)
        
        response_update_confidence = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(getiing_invoicedata), headers = utils.API_V2_HEADER)
        print(response_update_confidence)
    
    except Exception as error:
        print(error)
    
    return None


def extraction_handler(event):
    vendor_name = event.get('name')
    customer_id = event.get('receiverEmail')
    invoiceid=event.get('invoiceId')
    uploadby = event.get('uploadBy')
    sourceevent=event.get('source')
    senderEmail=quote(customer_id)
    customer_check=False
    invoicedata=get_invoice_handler.get_invoiceby(invoiceid)
    print(invoicedata)
    orgId=invoicedata.get('orgId')
    if sourceevent =='Web':
        customer_id = event.get('receiverEmail')
        customer_check=True
    else:
        pass
    
    static_engine_entities = {}
    if is_vendor_present(vendor_name) is False:
        print('Vendor name neither found from email nor provided by user')
        print('Detecting entities using Static Extraction Engine')
        static_engine_entities = static_extraction_handler(event)

        # Step 1 - Lookup supplier name with a valid PO number
        po_number = static_engine_entities.get('orderNumber', {}).get('value')
        # if po_number is not None and po_number=='':
        #     print(f'PO number found: {po_number}')
        #     # vendor_name = vendor_lookup_handler.handle({ 'customerId': customer_id, 'poNumber': po_number })
        # else:
        #     print('PO number not found')

        # Step 2 - Find if any of the names from supplier list present in Textract
        if is_vendor_present(vendor_name) is False:
            print('Supplier name not found')
            vendor_list = get_vendor_list_handler.handle({ 'customerId': customer_id })
            vendor_name = vendor_name_finder.find(event, vendor_list)
            print(vendor_name,'vendor_name check')
            print(customer_check,'customer_check')
            # vendor_name=vendor_name_finder.vendornameextract(event,vendor_list)
            GET_VENDOR_EMAIL=f'{utils.NODE_EXTRACTION_URL}/invoice/getVendorEmail?vendorName={vendor_name}&orgId={orgId}'
            get_response_http = requests.get(
            url=GET_VENDOR_EMAIL,
            headers = utils.API_V2_HEADER)
            print(get_response_http.status_code,'get_response_http')
            if get_response_http.status_code == 403:
                getinvoiceid=event['invoiceId']
                print('getinvoiceid',getinvoiceid)
                invoicedata=get_invoice_handler.get_invoiceby(getinvoiceid)
                print('it 403  is working')
                invoicedata['isVendorEmailExtracted']=0
                if uploadby =="Customer":
                    invoicedata['senderEmail']=invoicedata['receiverEmail']
                    
                print(json.dumps(invoicedata),'invoicedata')
                resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                print(resp.content,'resp.content','else condition')
                

            # elif get_response_http.status_code != 200:
            #     return []
                # print(f'Unable to get supplier email  for supplier {vendor_name}')
            elif get_response_http.status_code == 200:
                try:
                    get_response = get_response_http.json()
                    get_response_status = get_response.get('status')
                    if get_response_status != 'Success':
                        raise Exception(f'Unable to get supplier list for subscriber {customer_id}')
                    elif get_response_status == 'Success':
                        vendordata=get_response.get('data')
                        vendoremail=vendordata['vendorEmail']
                        print(vendoremail,'vendoremail')
                        
                        print(type(vendoremail),'vendoremail ')
                        if vendoremail==None:
                            vendoremail=""
                            
                        getinvoiceid=event['invoiceId']
                        print('getinvoiceid',getinvoiceid)
                        invoicedata=get_invoice_handler.get_invoiceby(getinvoiceid)
                        print('invoicedata1',invoicedata)
                         
                        if vendoremail !="" :
                            
                            
                            if uploadby =="Customer":
                    
                                invoicedata['senderEmail']=vendoremail
                                invoicedata['isVendorEmailExtracted']=1
                                print(json.dumps(invoicedata),'invoicedata')
                               
                                resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                                print(resp.content,'resp.content')
                        # elif vendoremail == None:
                        #     print('it none  is working')
                        #     invoicedata['isVendorEmailExtracted']=0
                        #     invoicedata['senderEmail']=invoicedata['receiverEmail']
                        #     print(json.dumps(invoicedata),'invoicedata')
                        #     resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                        #     print(resp.content,'resp.content','else condition')
                            
                            
                        else:
                            
                            # print('it is working')
                            invoicedata['isVendorEmailExtracted']=0
                            if uploadby =="Customer":
                                invoicedata['senderEmail']=invoicedata['receiverEmail']
                            print(json.dumps(invoicedata),'invoicedata')
                            resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                            print(resp.content,'resp.content','else condition')
                           
                except:
                    pass
                        
                            

    else:
        print(f'Supplier name found in invoice is {vendor_name}')


        # Step3 - Not yet Implemented
        
    dynamic_engine_entities = {}
    if is_vendor_present(vendor_name) is False:
        print('Vendor name neither found with PO not with Vendor list')
        vendor_name = utils.DEFAULT_VENDOR_NAME
    else:
        GET_VENDOR_EMAIL=f'{utils.NODE_EXTRACTION_URL}/invoice/getVendorEmail?vendorName={vendor_name}&orgId={orgId}'
        get_response_http = requests.get(
        url=GET_VENDOR_EMAIL,
        headers = utils.API_V2_HEADER)
        print(get_response_http.status_code,'get_response_http.status_codecheck2')
        if get_response_http.status_code == 403:
            getinvoiceid=event['invoiceId']
            print('getinvoiceid',getinvoiceid)
            invoicedata=get_invoice_handler.get_invoiceby(getinvoiceid)
            print('it 403  is working')
            invoicedata['isVendorEmailExtracted']=0
            if uploadby =="Customer":
                invoicedata['senderEmail']=invoicedata['receiverEmail']
            print(json.dumps(invoicedata),'invoicedata')
            resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
            print(resp.content,'resp.content','else condition')
            

        # elif get_response_http.status_code != 200:
        #     return []
            # print(f'Unable to get Vendor email  for Vendor {vendor_name}')
        elif get_response_http.status_code == 200:
            try:
                get_response = get_response_http.json()
                get_response_status = get_response.get('status')
                if get_response_status != 'Success':
                    raise Exception(f'Unable to get Vendor list for subscriber {customer_id}')
                elif get_response_status == 'Success':
                    vendordata=get_response.get('data')
                    vendoremail=vendordata['vendorEmail']
                    print(vendoremail,'vendoremail')
                    if vendoremail== None:
                        vendoremail= ""
                    getinvoiceid=event['invoiceId']
                    print('getinvoiceid',getinvoiceid)
                    invoicedata=get_invoice_handler.get_invoiceby(getinvoiceid)
                    if vendoremail != '' :
                        if uploadby =="Customer":
                            invoicedata['senderEmail']=vendoremail
                            invoicedata['isVendorEmailExtracted']=1
                            print(json.dumps(invoicedata),'invoicedata')
                           
                            resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                            print(resp.content,'resp.content')
                    # elif Vendoremail == None:
                    #     print('it none  is working')
                    #     invoicedata['isVendorEmailExtracted']=0
                    #     invoicedata['senderEmail']=invoicedata['receiverEmail']
                    #     print(json.dumps(invoicedata),'invoicedata')
                    #     resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                    #     print(resp.content,'resp.content','else condition')
                        
                        
                    else:
                        
                        print('it is working')
                        invoicedata['isVendorEmailExtracted']=0
                        if uploadby =="Customer":
                            invoicedata['senderEmail']=invoicedata['receiverEmail']
                        print(json.dumps(invoicedata),'invoicedata')
                        resp = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoicedata), headers = utils.API_V2_HEADER)
                        print(resp.content,'resp.content','else condition')
                       
            except:
                pass
                    
        
        print(f'Detecting entities using Dynamic Extraction Engine for {vendor_name}')
        dynamic_engine_entities = dynamic_extraction_handler(event, vendor_name,orgId)
    print('static_engine_entities:',static_engine_entities,'dynamic_engine_entities:',dynamic_engine_entities)

    # If there is no dictionary exists for the given Vendor in Email, use Static Extraction Engine
    if static_engine_entities == {} and dynamic_engine_entities == {}:
        static_engine_entities = static_extraction_handler(event)

    # Merge static and dynamic entities
    # merged_entities = static_engine_entities.copy()
    # if len(dynamic_engine_entities) > 0:
    #     merged_entities = dynamic_engine_entities.copy()
    
    merged_entities=getmergeentity(static_engine_entities,dynamic_engine_entities)

    return vendor_name, merged_entities

# Dynamic extraction engine with Vendor name must be provided
def dynamic_extraction_handler(event, vendor_name,orgId):
    event_copy = event.copy()
    event_copy['name'] = vendor_name
    event_copy['orgId']=orgId
    detected_entities = entity_detection_handler.handle(event_copy)
    return detected_entities
    
# Static extraction engine with no Vendor    
def static_extraction_handler(event):
    event_copy = event.copy()
    event_copy['name'] = ''
    event_copy['orgId']=''
    detected_entities = entity_detection_handler.handle(event_copy)
    return detected_entities

def is_vendor_present(vendor_name):
    if vendor_name is None or vendor_name == "" or vendor_name == utils.DEFAULT_VENDOR_NAME:
        return False
    return True
    
    
def extractingduedate(invoiceevent):
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = invoiceevent['documentDataPath']
    )

    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)
    print(document_json_list)


    # print(event['detectedEntities']['dueAmount']['value'],'check2')
    extractdays=document_json_list['documentData']
    mylist=['TERMS','Terms','Term','terms','Payment due:']
    workingdata=''
    try:
        for key,value in extractdays.items():
            if any(x in key for x in mylist) and key!='Terms of delivery:' and key!='Trade Terms:':
                adding_value=value
                adding_key=key
                workingdata=True

    except Exception as err:
        logging.exception( err)
        workingdata=False
        return invoiceevent

    try:
        addingnumber=[]
        print('adding_value',adding_value)
        # if extractdays=='TERMS' or extractdays=='Terms' or extractdays=='Terms of payment' or extractdays['documentData']=='Payment Terms':
        # top=event['documentData']
        
        special_characters=['%']
        special_characters_check=""
        
        if any(c in special_characters for c in adding_value):
            special_characters_check=True
            print("yes")
        
        else:
            special_characters_check=False
            print("no")
        print(special_characters_check)
        if special_characters_check is True:
        
            val=re.sub('^[a-zA-Z0-9]%*','',adding_value)
            # print(val)
        
            extractingnumber=re.findall(r'\d+', val)
            # print(extractingnumber)
        
        else:
            extractingnumber=re.findall(r'\d+', adding_value)
           
        # extractingnumber=re.findall(r'\d+', adding_value)
        print('extractingnumber',extractingnumber)
        if extractingnumber==[]:
            return 
        for i in extractingnumber:
            addingnumber.append(int(i))
            
        
        adding_number=max(addingnumber)
            
      
        # startdate=invoiceevent['detectedEntities']['invoiceDate']['value']
        getjobid=invoiceevent['invoiceId']
        print('getjobid',getjobid)
        toget_invoicedata=get_invoice_handler.get_invoiceby(getjobid)
        print('toget_invoicedata',toget_invoicedata)
        dueDatecheck=toget_invoicedata.get('dueDate','')
        try:
            if not dueDatecheck:
                startdate = toget_invoicedata['invoiceDate']
                print(startdate,'startdate')
                datestart=dattime.fromisoformat(startdate[:-1]).date()
                print(datestart,'check datestart')
                Begindate=parser.parse(str(datestart))
    

                Enddate = Begindate + dat.timedelta(days=int(adding_number))
                correct_date=Enddate.strftime('%Y-%m-%d')
                print(correct_date)
        
                toget_invoicedata['dueDate']=correct_date
            else:
                pass
        except Exception as err:
            logging.exception( err)
            correct_date=''
            # toget_invoicedata['dueDate']=""
            
            
        
        
        # enddate = pd.to_datetime(startdate) + pd.DateOffset(days=int(adding_number))
        # print(enddate,'checkme')

        # print(enddate.strftime('%m-%d-%Y'))
        
        # formateddate=enddate.strftime('%m-%d-%Y')
        # print('check',formateddate)
        
        
     
            
        response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(toget_invoicedata), headers = utils.API_V2_HEADER)
        print(response_update)



        # event['dueDate']=formateddate
    
        document_json_list['documentData'][adding_key]=correct_date
        print(document_json_list)

        s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        s3_client.put_object(
            Body = json.dumps(
                document_json_list,
                indent = 4,
                sort_keys = True
            ),
            Bucket = utils.BUCKET_NAME,
            Key = invoiceevent['documentDataPath']
        )
      
            

    except Exception as err:
        logging.exception( err)
        pass




    return invoiceevent
  
  
  
def invoiceconfidence(event): 
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = event['documentJsonPath']
    )

    document_json_str = document_json_s3_response.get('Body').read()
    response = json.loads(document_json_str)
    print(type(response))


    for i in response:

        blockvalue=i['Blocks']
    confidence=[]

    for block in blockvalue:
        if block['BlockType'] == "LINE":
            confidence.append(block['Confidence'])


    print(confidence)

    k=0
    for j in confidence:
        k=k+float(j)

    invoicedataconfidence=k/len(confidence)
    print("accuracy percent:",k/len(confidence))

    return invoicedataconfidence

def getmergeentity(static_entity,dynamic_entity):
    INVOICE_ENTIITES = [
        'invoiceNumber',
        'dueDate',
        'dueAmount',
        'orderNumber',
        'invoiceDate',
        'invoiceAmount',
        'taxTotal',
        'subTotal',
        'invoiceDescription',
        'totalAmount',
        'pst',
        'gst'
        
    ]

    new_item={}

    for i in INVOICE_ENTIITES:
        
        if i in dynamic_entity:
            print(i,'1')
            new_item[i]=dynamic_entity[i]
        elif i in static_entity:
            print(i,'2')
            new_item[i]=static_entity[i]
            
            
    print(new_item)
    return new_item

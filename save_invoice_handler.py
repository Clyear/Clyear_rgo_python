import json
import utils
import logging
import requests
import boto3
import datetime
import re
from collections import OrderedDict
import get_invoice_handler
from dateutil import parser

logger = logging.getLogger()

# Private lambda - doesn't return http response
def handle(event, context):
    # try:
    #     extractingduedate(event)
    # except:
    #     print(error)
    #     pass
 
    try:
        print(f'Save invoice event: {event}')
        
        document_name = save_invoice(event)
    except Exception as error:
        logger.error(f'Unable to create/update invoice: {str(error)}')
        raise ValueError(error)

    return {
        'msg': 'Success',
        'documentName': document_name
    }
    

def save_invoice(event):
    # Get event data
    detected_entities = event.get('detectedEntities', {})
    document_json_path = event.get('documentJsonPath')
    document_data_path = event.get('documentDataPath')
    document_name = event.get('documentName')
    supplier_name = event.get('vendorName')
    
    
    checkinginvoiceid=event['invoiceId']
    print('checkinginvoiceid',checkinginvoiceid)
    checkinvoice=get_invoice_handler.get_invoiceby(checkinginvoiceid)
    
    print('checkinvoice',checkinvoice)

    # Compute invoice data
    invoice_data = event.copy()
    invoice_data = update_invoice_entities(invoice_data, detected_entities)
    
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
    Bucket = utils.BUCKET_NAME,
    Key = invoice_data['documentDataPath']
    )
            
    document_json_str = document_json_s3_response.get('Body').read()    
    document_json_list = json.loads(document_json_str)
    print(document_json_list)
    
    val1=document_json_list['documentData']
    
    try:
        for k,v in val1.items():
            
            try:
                s1=v.replace("$","")
            except:
                pass
            try:
                
                s1=s1.replace(",","")
            except:
                pass
            try:
                s1=s1.strip()
            except:
                pass
            
            document_json_list['documentData'][k]=s1
    except Exception as err:
        logging.exception( err)
        pass
    
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
    Body = json.dumps(
    document_json_list,
    indent = 4,
    sort_keys = True
    ),
    Bucket = utils.BUCKET_NAME,
    Key = invoice_data['documentDataPath']
    )

    # Create & store invoice data
    invoice_data['senderEmail']=checkinvoice['senderEmail']
    invoice_data['isVendorEmailExtracted']=checkinvoice['isVendorEmailExtracted']
    
    invoice_data['textractJson'] = utils.get_http_s3_path(document_json_path)
    invoice_data['formValuesJson'] = utils.get_http_s3_path(document_data_path)
    # invoice_data['formJson'] = document_data_path
    invoice_data['tableValuesJson'] = utils.get_http_s3_path(document_data_path.replace('form', 'table'))
    invoice_data['name'] = supplier_name
    invoice_data['success'] = True
    invoice_data['textractFailed'] = False
    invoice_data['manualExtractFailed'] = False
    invoice_data['extractEngineFailed'] = False
    # invoice_data['status'] = 'Pending'

    invoice_data['errorMessage'] = 'Success'
    invoice_data['isSuccess'] = True
    invoice_data['errorCode'] = '200'
    
    print(f'Saving invoice with {invoice_data}')
    res = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(invoice_data), headers = utils.API_V2_HEADER)
    print(res.content)

    return document_name

def update_invoice_entities(invoice_data, detected_entities):
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
    Bucket = utils.BUCKET_NAME,
    Key = invoice_data['documentDataPath']
    )
    
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)
    print(document_json_list)
    for name, entity in detected_entities.items():
        
        invoice_data[name] = entity.get('value', None)
        
        if  name=='dueAmount' or name=='taxTotal'  or name=='subTotal':
            value_of_amount=entity.get('value')
            lable_of_amount=entity.get('label')
            
           


            # print(event['detectedEntities']['dueAmount']['value'],'check2')
            # extractdays=document_json_list['documentData']
            # print(float(value_of_amount))
            try:
                s1=re.sub("[^0-9.],*","",value_of_amount).strip()
                print(s1,'strings1')
                try:
                    ress = "{:.2f}".format(float(s1))
                except:
                    ress=s1
                    pass
                print(ress)
                invoice_data[name] = ress
                document_json_list['documentData'][lable_of_amount]=ress
            except Exception as err:
                logging.exception( err)
                invoice_data[name] = entity.get('value', None)
                
                
                
        elif name=='invoiceDate':
            try:
                invoice_date=entity.get('value')
                print(invoice_date)
                date_label=entity.get('label')
                
                datemod=parser.parse(str(invoice_date)).date()
                print(datemod,'datemod')
                invoice_data[name] = str(datemod)
                document_json_list['documentData'][date_label]=str(datemod)
            except:
                invoice_data[name] = entity.get('value', None)
            
        
        elif name=='dueDate':
            try:
                date_values=entity.get('value')
                print(date_values)
                date_label=entity.get('label')
                updated_date=parser.parse(str(date_values)).date()
                invoice_data[name] = str(updated_date)
                document_json_list['documentData'][date_label]=str(updated_date)
            except:
                invoice_data[name] = entity.get('value', None)
                
                
        elif name=='invoiceAmount':
            try:
                invoiceamount=entity.get('value')
                try:
                    if invoiceamount:
                        for currcheck in utils.currencylist1:
                            if currcheck in invoiceamount:
                                if currcheck=='BZR':
                                    currcheck='BRL'
                                elif currcheck=='CA':
                                    currcheck='CAD'

                                invoice_data['invoiceCurrency']=currcheck
                                
                except Exception as err:
                    logging.exception(err)
                            
                value_of_invoiceamount=entity.get('value')
                lable_of_invoiceamount=entity.get('label')
                try:
                    s1=re.sub("[^0-9.],*","",value_of_invoiceamount).strip()
                    print(s1,'strings1')
                    try:
                        ress = "{:.2f}".format(float(s1))
                    except:
                        ress=s1
                        pass
                    print(ress)
                    invoice_data[name] = ress
                    document_json_list['documentData'][lable_of_invoiceamount]=ress
                    
                except Exception as err:
                    logging.exception( err)
                    invoice_data[name] = entity.get('value', None)
                        
                            
                
            except Exception as err:
                logging.exception( err)
                invoice_data[name] = entity.get('value', None)
                
        
                
                
               

        else:
            invoice_data[name] = entity.get('value', None)
            
    try:
        subtotal=invoice_data['subTotal']
        print('subtotal',subtotal)
        if subtotal and subtotal !='0.00':
            if 'taxTotal' in detected_entities:
                
                taxtotal=detected_entities['taxTotal']['value']
                label_of_taxtotal=detected_entities['taxTotal']['label']
                print('taxtotal',taxtotal,'label_of_taxtotal',label_of_taxtotal)
                if '%' in taxtotal:
                    removal_percentage=taxtotal.replace('%', "")
                    taxtotal=removal_percentage.strip()
                    print(taxtotal,'percentage')
                    taxtoalcalculate=(float(taxtotal)/100)*float(subtotal)
                    print(taxtoalcalculate,'taxtoalcalculate')
                    invoice_data['taxTotal']=str(taxtoalcalculate)
                else:
                    try:
                        s1=re.sub("[^0-9.],*","",taxtotal).strip()
                        print(s1,'strings1')
                        try:
                            ress = "{:.2f}".format(float(s1))
                        except Exception as e:
                            logging.exception(e)
                            ress=s1
                            pass
                        print(ress)
                        invoice_data['taxTotal'] = ress
                        document_json_list['documentData'][label_of_taxtotal]=ress
                    except Exception as err:
                        logging.exception( err)
                        invoice_data['taxTotal'] = taxtotal
        
        else:
            if 'taxTotal' in detected_entities:
                
                taxtotal=detected_entities['taxTotal']['value']
                label_of_taxtotal=detected_entities['taxTotal']['label']
                if '%' in taxtotal:
                    invoice_data['taxTotal']=0
                else:
                    try:
                        s1=re.sub("[^0-9.],*","",taxtotal).strip()
                        print(s1,'strings1')
                        try:
                            ress = "{:.2f}".format(float(s1))
                        except:
                            ress=s1
                            pass
                        print(ress)
                        invoice_data['taxTotal'] = ress
                        document_json_list['documentData'][label_of_taxtotal]=ress
                        
                    except Exception as err:
                        logging.exception( err)
                        invoice_data['taxTotal'] = taxtotal
                        
    except Exception as e:
        logging.exception(e)

        
    try:
        
        gettaxtotal=invoice_data.get('taxTotal','')
        
        try:
            gst=detected_entities['gst']['value']
            gst_label=detected_entities['gst']['label']
        except Exception as e:
            logging.exception(e)
            gst=''
        try:
            pst=detected_entities['pst']['value']
            pst_label=detected_entities['pst']['label']
            
        except Exception as e:
            logging.exception(e)
            pst=''
            
        
            
        
        # print(gst,pst,'pst,gst')
        subtotal=invoice_data['subTotal']
        
        if gst:
            if '%' in gst:
                if subtotal  and subtotal!='0.00':
                    removal_percentage_gst=gst.replace('%', "")
                    gst=removal_percentage_gst.strip()
                    gst=(float(gst)/100)*float(subtotal)
                    invoice_data['gst']=str(gst)
                    document_json_list['documentData'][gst_label]=str(gst)
                    
                else:
                    gst=''
            else:
                gst=re.sub("[^0-9.],*","",gst).strip()
                print(gst,'gst1')
            
                invoice_data['gst']=str(float(gst))
                document_json_list['documentData'][gst_label]=str(float(gst))
        if pst:
            print(pst,'pst')
            if '%' in pst:
                print(subtotal)
                if subtotal and subtotal!='0.00':
                    removal_percentage_pst=pst.replace('%', "")
                    pst=removal_percentage_pst.strip() 
                    pst=(float(pst)/100)*float(subtotal)
                    invoice_data['pst']=str(pst)
                    document_json_list['documentData'][pst_label]=str(pst)
                else:
                    pst=''
                #     pst=re.sub("[^0-9.],*","",pst).strip()
                #     print(pst,'strings1')
                    
            
            else:
                
                pst=re.sub("[^0-9.],*","",pst).strip()
                print(pst,'pst1')
                # try:
                #     ress = "{:.2f}".format(float(s1))
                # except Exception as e:
                #     logging.exception(e)
                    # ress=s1
                invoice_data['pst']=str(float(pst))
                document_json_list['documentData'][pst_label]=str(float(pst))
               
                
    except Exception as e:
        logging.exception (e)   
    print(gst,pst,'gstpst')
    if not gettaxtotal or gettaxtotal=='0.00' :
        if gst and pst:
            try:
                invoice_data['taxTotal']=str(float(gst)+float(pst))
            except Exception as e:
                logging.exception(e)

        if gst and not pst:
            try:
                invoice_data['taxTotal']=str(float(gst))
            except Exception as e:
                logging.exception(e)
        if pst and not gst:
            print(pst)
            try:
                
                invoice_data['taxTotal']=str(float(pst))
            except Exception as e:
                logging.exception(e)
    

    document_json_list['detectedEntities']=detected_entities            
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
        Body = json.dumps(
        document_json_list,
        indent = 4,
        sort_keys = True
        ),
        Bucket = utils.BUCKET_NAME,
        Key = invoice_data['documentDataPath']
    )
        

                
                
                
         
                
        
        
    return invoice_data
    
    
def try_parsing_date(text):
    from datetime import datetime
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y','%m/%d/%Y','%d/%m/%y','%m/%d/%Y','%m/%d/%y','%d/%m/%Y'):
        try:
            val=datetime.strptime(text, fmt)
            val2=val.strftime('%Y-%m-%d')
            print(val2,'check')
            return val2
            
        except ValueError:
            pass
    raise ValueError('no valid date format found')
  
    
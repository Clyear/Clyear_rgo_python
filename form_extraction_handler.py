import json
import boto3
import utils
import logging
from collections import OrderedDict
from document import TDocument
import re
import datetime
comprehend_client = boto3.client('comprehend')

def handle(event, context):
    document_json_path = event.get('documentJsonPath')
    
    # Bad request if extracted document json path not found
    if document_json_path is None and document_json_path == "":
        raise ValueError('Extracted document json path not found')

    form_values_file_path = None
    try:        
        # Extract form values as key value pair in a linear json
        form_values , extractlanguangecode = extract_form_values(document_json_path)
        print('form_values',form_values,'extractlanguangecode',extractlanguangecode)
        form_values = {
            'documentData': form_values
        }
        print(form_values)
        try:
            form_values=taxtrimming(form_values)
            form_values={
                'documentData':form_values
                
            }
        except Exception as e:
            logging.exception(e)

        
        # Store form values as json in S3
        form_values_file_path = store_form_values(form_values, document_json_path)
    except Exception as error:
        logging.error(str(error))
        raise ValueError(error)

    return {
        'formValuesFilePath': form_values_file_path,'extractlanguangecode':extractlanguangecode
    }



# Extract form values as key value pair in a linear json
def extract_form_values(document_json_path):
    # Read document json content from S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = document_json_path
    )
    
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)
    try:
        extractlanguangecode=extractlanguange(document_json_list)
    except Exception as e:
        logging.exception(e)
        extractlanguangecode=''

    # Extract form values from document json content
    parent_document = None    
    for document in document_json_list:
        if parent_document is None:
            parent_document = TDocument(**document)
            continue
        current_document = TDocument(**document)
        parent_document.blocks.extend(current_document.blocks)

    page_blocks = parent_document.pages()
    form_values = parent_document.form_values(page_blocks)
    # try:
    #     form_values=extractingduedate(form_values)
    # except:
    #     pass
    try:
        form_values = {key.replace('+','').strip(): item for key, item in form_values.items()}
    except Exception as e:
        logging.error(e)
        pass
        
    ordered_form_values = OrderedDict(sorted(form_values.items()))
    
    return ordered_form_values , extractlanguangecode
    

# Store form values as json in S3
def store_form_values(form_values, document_json_path):
    form_values_file_path = '-form-values'.join(document_json_path.rsplit('-textracted', 1))
    logging.info(f'Storing form values as json in {form_values_file_path}')
    
    # Store form_values as json in S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
        Body = json.dumps(
            form_values,
            indent = 4,
            sort_keys = True
        ),
        Bucket = utils.BUCKET_NAME,
        Key = form_values_file_path
    )
    
    return form_values_file_path    

def taxtrimming(ches):
    mynewdict={}
    for i,j in ches['documentData'].items():
        input_string = re.sub(r"\([^\)]*\)", "", i)

        # Remove special characters
        input_string = re.sub(r"[^\w\s]", "", input_string)

        # Remove words inside brackets


        input_string = re.sub(r"\d+", "", input_string)

        res = re.sub(' +', ' ', input_string)
        if res :
            if res.lower().strip() in utils.taxKeyList:
                mynewdict[res.strip()]=j
            elif res.lower().strip() in utils.pstlist:
                mynewdict[res.strip()]=j
            elif res.lower().strip() in utils.gstlist:
                mynewdict[res.strip()]=j
            else:
                mynewdict[i]=j
                
                
                
                
                
        
   
    print('mynewdict',mynewdict)        
    return mynewdict

def extractlanguange(data):
    extracted_text = ''
    for block in data:
        getblock=block['Blocks']
        for lin in getblock:
            
            if lin['BlockType'] == 'LINE':
                extracted_text += lin['Text'] + ' '

    # Use Comprehend to detect the language
    language_response = comprehend_client.detect_dominant_language(Text=extracted_text)
    detected_language = language_response['Languages'][0]['LanguageCode']
    if detected_language:
        return detected_language
    else:
        return ''

# def extractlanguange(data):
#     extracted_text = ''
#     for block in data:
#         getblock=block['Blocks']
#         for lin in getblock:
            
#             if lin['BlockType'] == 'LINE':
#                 extracted_text += lin['Text'] + ' '

#     # Use Comprehend to detect the language
#     language_response = comprehend_client.detect_dominant_language(Text=extracted_text)
#     detected_language = language_response['Languages'][0]['LanguageCode']
#     if detected_language:
#         return detected_language
#     else:
#         return ''

# def extractingduedate(formvalues):
#     # print('event of extrraction',event)
#     # s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
#     # document_json_s3_response = s3_client.get_object(
#     #     Bucket = utils.BUCKET_NAME,
#     #     Key = event['documentDataPath']
#     # )

#     # document_json_str = document_json_s3_response.get('Body').read()
#     # document_json_list = json.loads(document_json_str)
#     # print(document_json_list)


#     # # print(event['detectedEntities']['dueAmount']['value'],'check2')
#     # extractdays=document_json_list['documentData']
#     date_format_list=['invoice date','date','INVOICE DATE','Invoice Date','Date','DATE','Invoice date','invoice Date','Date Printed']
#     mylist=['TERMS','Terms','Terms of payment','Payment Terms','Terms of payment:','Payment Terms:']
#     workingdata=''
#     try:
#         for k,value in formvalues.items():
#             if k in mylist:
#                 adding_value=value
#                 adding_key=k
#                 workingdata=True

#     except:
#         workingdata=False
#         return event
#     try:
#         for K,V in formvalues.items():
#             if K in date_format_list:
#                 startingdate=V
#                 starting_date_key=K

#     except:
#         pass
    
#     try:

#         print('adding_value, adding_key',adding_value,adding_key)
#         # if extractdays=='TERMS' or extractdays=='Terms' or extractdays=='Terms of payment' or extractdays['documentData']=='Payment Terms':
#         # top=event['documentData']
#         extractingnumber=re.findall(r'\d+', adding_value)
#         print('extractingnumber',extractingnumber)
#         adding_number=max(extractingnumber)
#         print(adding_number)
#         # startdate=event['detectedEntities']['invoiceDate']['value']
#         # getjobid=invoiceevent['invoiceId']
#         # print('getjobid',getjobid)
#         # toget_invoicedata=get_invoice_handler.get_invoiceby(getjobid)
#         # print('toget_invoicedata',toget_invoicedata)
#         # startdate = toget_invoicedata['invoiceDate']
#         # print(startdate,'startdate')
        
        
#         # enddate = pd.to_datetime(startdate) + pd.DateOffset(days=int(adding_number))
#         # print(enddate,'checkme')

#         # print(enddate.strftime('%m-%d-%Y'))
        
#         # formateddate=enddate.strftime('%m-%d-%Y')
#         # print('check',formateddate)
        
#         Begindate = datetime.datetime.strptime(startingdate, "%m/%d/%Y")
  

#         Enddate = Begindate + datetime.timedelta(days=int(adding_number))
#         correct_date=Enddate.strftime('%m/%d/%Y')
#         print(correct_date)



#         # event['dueDate']=formateddate
#         formvalues[adding_key]=correct_date
#         # print(document_json_list)
#         # document_json_lists=document_json_list['documentData']
        
#         # document_json_list=OrderedDict(sorted(document_json_lists.items()))
#         # form_values = {
#         #     'documentData': document_json_list
#         # }
#     #     print(document_json_list)
#     #     print('event',event['documentDataPath'])
#     #     key_path=event['documentDataPath']
#     #     s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
        
#     #     s3_client.put_object(
#     #     Body = json.dumps(
#     #             form_values,
#     #             indent = 4,
#     #             sort_keys = True
#     #     ),
#     #     Bucket = utils.BUCKET_NAME,
#     #     Key = key_path
#     #     )

#     except:
#         pass




#     return formvalues 

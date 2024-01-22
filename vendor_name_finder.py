import json
import utils
import boto3
import difflib
from document import TDocument
from fuzzywuzzy import process
from PyPDF4 import PdfFileReader
from io import BytesIO
import logging

def find(event, VENDOR_list):
    print('Finding similarity match of supplier names in the invoice')

    try:
        vendor_name=vendornameextract(event,VENDOR_list)
        print(vendor_name,'vendor_name level1')
    except Exception as e:
        logging.exception(e)
        vendor_name=None
    if not vendor_name:
        try:
            vendor_name=doublelinevendorname(event,VENDOR_list)
        except Exception as e:
            logging.exception(e)
            vendor_name=None
            
    print(f'Supplier name found with similarity match is {vendor_name}')
    
    return vendor_name
    
    
def vendornameextract(event,VENDOR_list):
    if not  VENDOR_list:
        
        return None
    document_json_path = event.get('documentJsonPath')
    client = boto3.client('textract')
    print(document_json_path,'document_json_path')
    
    # filenameupdate=document_json_path.replace('-textracted.json','')
    # print(filenameupdate)


    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = document_json_path
    )
    # percentagevaluelist=[]
    # newvendorList=[]
    
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)
    percentagevaluelist=[]
    # newvendorList=[]
    contentlist=[]
    comparelist=[]
    comparelist1=[]
    for document in document_json_list:
        block_value=document['Blocks']
    for block in block_value:
        if block['BlockType']=='LINE':
        # print(block['Text'])
            contentlist.append(block['Text'].strip())
        
    print(contentlist,'contentlist')
    for vendorName in VENDOR_list:
        comparelist1.append({vendorName:process.extractOne(vendorName,contentlist)[1]})
    print(comparelist1,'comparelist1')
    
    for key in comparelist1:
        # print(key.values(),'key')
        for k,v in key.items(): 
            percentagevaluelist.append(v)
        
    maxvalueofpercentagelist=max(percentagevaluelist)

    print(maxvalueofpercentagelist) 
    mydicy={}
    keylist=[]
    for m in comparelist1: 
        for key,values in m.items():
            # print(values,'values')
            if values==100:
                mydicy[key]=values
                keylist.append(key)
    # dictcomparelist=dict(comparelist)
    print(mydicy)
    print(keylist)

    suppliername=''
    if not keylist:
        suppliername=None
    else:
        for findvalue in keylist:
            if findvalue in VENDOR_list:
                suppliername=findvalue
        
        
                
                
                
    print('suppliername:',suppliername)
    return   suppliername

def doublelinevendorname(event,VENDOR_list):
    filename_vendor = event.get('documentJsonPath',None)
    print(filename_vendor,'filename_vendor')
    if not filename_vendor:
        return None
    filename_vendor=filename_vendor.replace('-textracted.json', '')
    print(filename_vendor,'filename_vendor')
    document_verification=checkdocument(filename_vendor)
    if document_verification:    
    
        toget_jobid=analyse_expense(filename_vendor)
        analyzelist=listen_expense_analysis(toget_jobid)
        vendor_list=[]
        for a in analyzelist:
        
            combine_document=a['ExpenseDocuments']
            
            for b in combine_document:
                summar_document=b['SummaryFields']
                for c in summar_document:
                    if c['Type']['Text']=='VENDOR_NAME':
                        # print(c['ValueDetection']['Text'],'check')
                        vendor_nAME=c['ValueDetection']['Text']
                        vendor_nAME=vendor_nAME.replace("\n"," ")
                        vendor_list.append(vendor_nAME)
                        
        print(vendor_list,'vendor_list')
        newVendorlist= [x.lower() for x in VENDOR_list]
        vendorName=None                
        for vendor in vendor_list:
            if vendor.lower() in newVendorlist:
                print(vendor,'vendor')
                
                vendorName=VENDOR_list[newVendorlist.index(vendor.lower())]
                
        
        return vendorName
    else:
        return None
            
    
            
                    
                    
                    
                    

def analyse_expense(document_name):
    document_location = {
        'S3Object': {
            'Bucket': utils.BUCKET_NAME,
            'Name': document_name
        }
    }
    
    textract_client = boto3.client('textract')
    expense_response = textract_client.start_expense_analysis(
        DocumentLocation = document_location,
        NotificationChannel = {
            "SNSTopicArn": "arn:aws:sns:us-east-1:637423465315:Currencylistener",
            "RoleArn": "arn:aws:iam::637423465315:role/AWS-TextractionCurrency-SNS"
        }
    )
    expense_job_id = expense_response.get('JobId')
    # logging.info(f'Expense analysis job started: JobId: {expense_job_id}')
    
    return expense_job_id

def listen_expense_analysis(analysis_job_id):
    textract_client = boto3.client('textract')

    # Get aggregated response from expense analysis
    analysis_result = textract_client.get_expense_analysis(JobId = analysis_job_id)
    print(analysis_result.get('JobStatus'),'analysis_result')
    resultcheck=analysis_result.get('JobStatus')
    while resultcheck!='SUCCEEDED'  :
        analysis_result = textract_client.get_expense_analysis(JobId = analysis_job_id)
        resultcheck=analysis_result.get('JobStatus')
        # print(resultcheck,'resultcheck2')   
    analysis_result_list = [analysis_result]
    # print(analysis_result_list,'analysis_result_list')
    
    while 'NextToken' in analysis_result:
        analysis_result = textract_client.get_expense_analysis(
            JobId = analysis_job_id,
            NextToken = analysis_result.get('NextToken')
        )
        analysis_result_list.append(analysis_result)
    print(type(analysis_result_list))
    return analysis_result_list

    

    
    

    


def extract_content(document_json_path):
    # Read document json content from S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = document_json_path
    )
    
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)

    # Extract form values from document json content
    parent_document = None    
    for document in document_json_list:
        if parent_document is None:
            parent_document = TDocument(**document)
            continue
        current_document = TDocument(**document)
        parent_document.blocks.extend(current_document.blocks)

    page_blocks = parent_document.pages()
    content = parent_document.content(page_blocks)
    return content
    
def find_similar_vendor_name(content, VENDOR_list):
    content_tokens = [x.lower() for x in content.split(' ')]

    similar_name_dict = {}
    for vendor_name in VENDOR_list:
        supplier_tokens = [x.lower() for x in vendor_name.split(' ')]

        similar_tokens = []
        for token in supplier_tokens:
            similar_token = difflib.get_close_matches(token, content_tokens, n=1)
            if len(similar_token) == 1:
                similar_tokens.extend(similar_token)
        
        similar_name = ' '.join([x for x in similar_tokens])
        similar_name_dict[similar_name] = vendor_name
    print(f'Computed similar name dictionary: {similar_name_dict}')

    if len(similar_name_dict) == 0:
        return None
        
    try:
        max_similarity = 0
        max_similar_name = None
        for similar_name, vendor_name in similar_name_dict.items():
            sequence_matcher = difflib.SequenceMatcher(None, vendor_name.lower(), similar_name)
            sequence_matcher.get_matching_blocks()
            similarity_ratio = sequence_matcher.ratio()
            if max_similarity < similarity_ratio:
                max_similarity = similarity_ratio
                max_similar_name = similar_name
    
        max_similarity = round(max_similarity * 100, 2)
        matched_vendor_name = similar_name_dict[max_similar_name]
        print(f'{max_similarity}% match found with "{max_similar_name}" for Supplier "{matched_vendor_name}"')
    
        if max_similarity >= 80:
            return matched_vendor_name
    except:
        return None

    return None



def checkdocument(Keys):

    document_status=''
    client = boto3.client('s3')

    response=client.get_object(Bucket=utils.BUCKET_NAME,Key=Keys)

    data=response['Body'].read()
    document_status=False
    # print(data)
    # pdf = PdfFileReader(BytesIO(data))
    # print(pdf)
    try:
        pdf = PdfFileReader(BytesIO(data))
        document_status=True

    except Exception as err:
        # logging.exception( err)
        
        pass
    print(document_status)
    return document_status




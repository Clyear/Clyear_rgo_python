

import utils
import json
import logging
import boto3
import get_invoice_handler





def handle(event):
    invoiceid=event.get('invoiceId')
    
    
    invoicedata=get_invoice_handler.get_invoiceby(invoiceid)
    invoiceCurrency=invoicedata.get('invoiceCurrency','')
    
    if not invoiceCurrency:
        getwordlist= getworddata(invoicedata)
        
        ### step1 check static array with word list
        
        
        for curr in utils.currencylist:
            if curr in getwordlist:
                invoiceCurrency=str(curr)
            else:   
                textract_currency=gettextractcurrency(invoicedata)
                if textract_currency:
                    invoiceCurrency=str(textract_currency)
                    
                    
    return invoiceCurrency
                    
                
                    
                    
                
            
            
            
    
    
    
    
    
    
    

def getworddata(event):
    
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
    
    return contentlist
def gettextractcurrency(invoicedata):
    
    filename=invoicedata.get('filePath',None)
    if filename:
        filename=filename.replace('https://apar-invoice.s3.amazonaws.com','')
        getjobid=analyse_expense(filename)
        listenanalysis=listen_expense_analysis(getjobid)
        
        currencylisy=[]
        for i in listenanalysis:
            
            expense=i['ExpenseDocuments']
            
            for j in expense :
                summaryfiels=j['SummaryFields']
                # print(summaryfiels)
                
            for kc in summaryfiels:
                try:
                    print(kc['Currency'])
                    currencylisy.append(kc['Currency']['Code'])
                except:
                    continue
    if  currencylisy:
        return max(currencylisy)
    else:
        return ''         
                
    
        


def analyse_expense(filename):
    document_location = {
        'S3Object': {
            'Bucket': utils.BUCKET_NAME,
            'Name': filename
        }
    }
    
    textract_client = boto3.client('textract')
    expense_response = textract_client.start_expense_analysis(
        DocumentLocation = document_location,
        NotificationChannel = {
            "SNSTopicArn": "arn:aws:sns:us-east-1:328326462997:AmazonTextractDocumentAnalysis",
            "RoleArn": "arn:aws:iam::328326462997:role/AWSTextract-SNSPublishRole"
        }
      
    )
    expense_job_id = expense_response.get('JobId')
    # logging.info(f'Expense analysis job started: JobId: {expense_job_id}')
    
    return expense_job_id

def listen_expense_analysis(analysis_job_id):
    textract_client = boto3.client('textract')

    # Get aggregated response from expense analysis
    analysis_result = textract_client.get_expense_analysis(JobId = analysis_job_id,MaxResults=123)
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
    # print(analysis_result_list)
   
    # jsstr=json.dumps(analysis_result_list)
    # f = open("demofile2.txt", "w+")
    # f.write(''.join(jsstr))
    # f.close()
    return analysis_result_list
    
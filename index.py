import json
import boto3
import logging

def handler(event,context):
    response={
        'statusCode':200,
        'body':'success'
        
    }
    
    print(event)
    if event['requestContext']['httpMethod']=='OPTIONS':
        return  response
    
    BUCKET_NAME= "cylear-invoices"
    
    DEFAULT_VALUE = 'N/A'
    
    headers = {
    "Access-Control-Allow-Headers" : "Access-Control-Allow-Methods, Access-Control-Allow-Origin, Content-Type, x-requested-with, Authorization",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*"
    }
    
    urlParams=event.get('queryStringParameters','')
    invoiceId=urlParams.get('invoiceId',None)
    emailId=urlParams.get('emailId','')
    vendorName=urlParams.get('vendorName','')
    toEmailId=urlParams.get('toEmailId',None)
    fileNameParam=urlParams.get('fileNameParam',None)
    action=urlParams.get('action',None)
    uploadBy=urlParams.get('uploadBy','')
    documentName=urlParams.get('documentName',None)
    folderName=urlParams.get('folderName','')
    fileName=urlParams.get('fileName','')
    orgId=urlParams.get('orgId','')
    invoiceSource=urlParams.get('invoiceSource','Web')
    s3filePath=f'https://{BUCKET_NAME}.s3.amazonaws.com/{documentName}'
    initialData = {
        'vendorName': vendorName,
        'receiverEmail' : toEmailId,
        'filepath': s3filePath,
        'fileName': fileName,
        'folderName': folderName,
        'documentName': documentName,
        'orgId':orgId,
        'action': action,
        'uploadBy': uploadBy,
        'invoiceSource': invoiceSource
    }
    if invoiceId:
        initialData['trigger'] = 'dashboard_re_upload'
        initialData['status'] = 'Reprocessing'
        initialData['invoiceId'] = int(invoiceId)
        
        initialData['senderEmail'] = emailId
        
    else:
        initialData['trigger'] = 'dashboard_upload'
        initialData['status'] = 'Processing'
        initialData['senderEmail'] = emailId
        
    # lambda_params={
    #     'FunctionName':'FileUploadStep2-save-invoice-handler',
    #     'InvocationType': 'RequestResponse',
    #     'Payload':json.dumps(initialData)
        
    # }
    
    # print(lambda_params,'lambda_params')
    try:
        print('[PROCESS]  lambda invoke started')
        client = boto3.client('lambda')
        docAnalysisResponse=client.invoke(FunctionName='FileUploadStep2-save-invoice-handler',InvocationType='RequestResponse',Payload=json.dumps(initialData))
        print(docAnalysisResponse,'docAnalysisResponse')
        print(type(docAnalysisResponse['Payload']))
        payload=docAnalysisResponse['Payload'].read()
        payload=payload.decode()
        print(payload,type(payload))
        # invoiceData=payload.get('body')
        # print(invoiceData)
        return { 'body': json.dumps({'success':True}), 'headers':headers, 'statusCode': 200}
    
    except Exception as e:
        print(e)
        print('[ERROR]  lambda invoke Failed')
        
    
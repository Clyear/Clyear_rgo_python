import os
import json
import utils
import boto3

def handle(analysis_job_id, s3_object_name):
    # Step1: Listen document analysis and get document json
    document_json = listen_document_analysis(analysis_job_id)
    
    # Step2: Store document analysis result in S3
    document_json_path = store_document_result(document_json, s3_object_name)

    # Step3: Call Extraction engine
    print('Calling extraction engine')
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName = 'extraction-engine-handler',
        InvocationType = 'Event',
        Payload = json.dumps({
            'analysisJobId': analysis_job_id,
            'documentJsonPath': document_json_path
        })
    )
    

# Listen document analysis and get document json
def listen_document_analysis(analysis_job_id):
    textract_client = boto3.client('textract')

    # Get aggregated response from document analysis
    analysis_result = textract_client.get_document_analysis(JobId = analysis_job_id)
    analysis_result_list = [analysis_result]
    
    while 'NextToken' in analysis_result:
        analysis_result = textract_client.get_document_analysis(
            JobId = analysis_job_id,
            NextToken = analysis_result.get('NextToken')
        )
        analysis_result_list.append(analysis_result)
        print(analysis_result_list)
    
    return analysis_result_list
    
    
# Store document analysis result in S3
def store_document_result(analysis_result_list, s3_object_name):
    # Frame S3 directory path
    file_root, file_ext = os.path.splitext(s3_object_name)
    file_type = file_ext.split('.')[1]
    analysis_result_file_path = f'{file_root}.{file_type}-textracted.json'
    print(f'Storing document analysis result in {analysis_result_file_path}')
    
    # Store analysis_result as json in S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
        Body = json.dumps(
            analysis_result_list,
            indent = 4,
            sort_keys = True
        ),
        Bucket = utils.BUCKET_NAME,
        Key = analysis_result_file_path
    )
    
    return analysis_result_file_path    
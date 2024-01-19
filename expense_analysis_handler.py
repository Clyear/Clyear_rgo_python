import os
import json
import utils
import boto3

def handle(analysis_job_id, s3_object_name):
    # Step1: Listen expense analysis and get expense json
    expense_json = listen_expense_analysis(analysis_job_id)
    
    # Step2: Store expense analysis result in S3
    expense_json_path = store_expense_result(expense_json, s3_object_name)

    # Step3: Call Extraction engine
    print('Calling line item extraction')
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName = 'expense-item-extraction-handler',
        InvocationType = 'Event',
        Payload = json.dumps({
            'expenseJobId': analysis_job_id,
            'expenseJsonPath': expense_json_path
        })
    )


# Listen expense analysis and get expense json
def listen_expense_analysis(analysis_job_id):
    textract_client = boto3.client('textract')

    # Get aggregated response from expense analysis
    analysis_result = textract_client.get_expense_analysis(JobId = analysis_job_id)
    analysis_result_list = [analysis_result]
    
    while 'NextToken' in analysis_result:
        analysis_result = textract_client.get_expense_analysis(
            JobId = analysis_job_id,
            NextToken = analysis_result.get('NextToken')
        )
        analysis_result_list.append(analysis_result)
    print(analysis_result_list)
    return analysis_result_list
    
    
# Store expense analysis result in S3
def store_expense_result(analysis_result_list, s3_object_name):
    # Frame S3 directory path
    file_root, file_ext = os.path.splitext(s3_object_name)
    file_type = file_ext.split('.')[1]
    analysis_result_file_path = f'{file_root}.{file_type}-textracted-table.json'
    extlist=['.png','.tiff','.jpg','.jpeg']
    for ext in extlist:
        if ext in analysis_result_file_path.lower():
            print(ext)
            analysis_result_file_path=analysis_result_file_path.replace(ext,'.pdf')
            
    print(f'Storing expense analysis result in {analysis_result_file_path}')
    
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
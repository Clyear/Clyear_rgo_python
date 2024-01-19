import json
import boto3
import utils
import table_util

def handle(event, context):
    document_json_path = event.get('expenseJsonPath')
    
    # Bad request if extracted document json path not found
    if document_json_path is None or len(document_json_path) == 0:
        raise ValueError('Extracted document json path not found')

            

    table_values_file_path = None
    try:        
        # Extract table values
        table_values = extract_table_values(document_json_path)
        table_values = {
            'tableData': table_values
        }
        print(table_values,'table_values34')
        
        # Store table values as json in S3
        table_values_file_path = store_table_values(table_values, document_json_path)
    except Exception as error:
        print(str(error))
        raise ValueError(error)

    return {
        'tableValuesFilePath': table_values_file_path
    }

# Extract table values
def extract_table_values(document_json_path):
    # Read document json content from S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = document_json_path.replace('-textracted.json', '-textracted-table.json')
    )
    
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)

    # Extract table values from document json content
    table_list = table_util.extract_expense_items(document_json_list)
    return table_list


# Store form values as json in S3
def store_table_values(table_values, document_json_path):
    extension=['.jpeg','.png','.tiff','.jpg']
    for ext in extension:
        if ext in document_json_path:
            document_json_path=document_json_path.replace(ext,'.pdf')
    table_values_file_path = '-table-values'.join(document_json_path.rsplit('-textracted-table', 1))
    print(f'Storing table values as json in {table_values_file_path}')
    
    # Store table_values as json in S3
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.put_object(
        Body = json.dumps(
            table_values,
            indent = 4,
            sort_keys = True
        ),
        Bucket = utils.BUCKET_NAME,
        Key = table_values_file_path
    )
    
    return table_values_file_path
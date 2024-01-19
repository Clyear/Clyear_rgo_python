import uuid
import boto3
import json

# Sends invoice message to SQS
def handle(event, context):
    try:
        event_param = {}
        query_string_param = event.get('queryStringParameters')
        if query_string_param is not None:
            method = event.get('requestContext', {}).get('http', {}).get('method')
            if method == 'OPTIONS':
                return None
            event_param = query_string_param
        else:
            event_param = event
    
        invoice_id = event_param.get('invoiceId')
        message_group_id = event_param.get('userId', 'invoice-message')
    
        # Get the queue
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=f'round-robin-invoice-queue.fifo')
    
        # Send message    
        queue.send_message(
            MessageBody=json.dumps({
                'invoiceId': invoice_id
            }),
            MessageGroupId=message_group_id,
            MessageDeduplicationId=str(uuid.uuid4())
        )
        print(f'Sent invoice {invoice_id} to round-robin-invoice-queue.fifo')
    
        return{
            'body': json.dumps({
                'success': True
            }),
            'statusCode': 200
            }
            
    except:
        return{
            'body': json.dumps({
                'success': True
            }),
            'statusCode': 200
            }
        
        
    
    
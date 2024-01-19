import boto3
import uuid
import time

def handle(event, context):
    print(event)
    message_body = event['Records'][0]['body']
    event_source_arn = event['Records'][0]['eventSourceARN']
    queue_name = event_source_arn.split(':')[-1]
    
    print(f'Passing {message_body}')
    time.sleep(2)
    
    # Get the service resource
    sqs = boto3.resource('sqs')
    message_id = str(uuid.uuid4())
    # Get the queue
    queue = sqs.get_queue_by_name(QueueName='invoice-ordered.fifo')
    queue.send_message(
        MessageBody=message_body,
        MessageGroupId=message_body[0],
        MessageDeduplicationId=message_id
    )
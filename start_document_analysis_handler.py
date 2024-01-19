import os
import json
import boto3
import utils
import logging

import pdf_converter_handler
import analyse_document_starter
import save_invoice_handler
import get_invoice_handler

logger = logging.getLogger()

# Private lambda - doesn't return http response
def handle(sqs_event, context):
    # Get invoice id from the SQS event
    event_message = json.loads(sqs_event['Records'][0]['body'])
    invoice_id = event_message['invoiceId']
    print(f'Start processing invoice {invoice_id}')
    if invoice_id is None:
        return

    # Get invoice record using invoice id
    event = invoice = get_invoice_handler.handle(invoice_id)
    if invoice is None:
        print(f'[ERROR] Invoice with id {invoice_id} not found')
        return

    file_name = event.get('fileName')
    file_root, file_ext = os.path.splitext(file_name)
    
    # Bad request, if file is not in supported format
    if file_ext.lower() not in utils.SUPPORTED_FILE_EXT:
        print(f'{file_ext} is not a supported file format')
        return utils.create_response(400, f'{file_ext} is not a supported file format')

    try:
        # Step 1 - Convert to pdf - Update file / document name
        if file_ext.lower() in utils.SUPPORTED_PDF_CONVERSIONS:
            converter_response = pdf_converter_handler.handle(event, context)
            event.update(converter_response)
            print(f'Updated event after pdf conversion: {event}')
        
        # Step 2 - Start document analysis - Update analysis job id
        document_analysis_response = analyse_document_starter.handle(event, context)
        event.update(document_analysis_response)
        print(f'Updated event after start document analysis: {event}')
        
        # Step 3 - Create/Update invoice with new document analysis job id
        invoice = save_invoice_handler.handle(event, context)
        print(f'Created/Updated invoice: {invoice}')
    except Exception as error:
        logger.error(f'Unable to start document analysis {str(error)}')
        return utils.create_response(500, f'Unable to start document analysis: {str(error)}')
        
    return utils.create_200_response(invoice)

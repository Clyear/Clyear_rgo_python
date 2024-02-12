import re
import json
import base64
import quopri
import utils
import os
import boto3
import logging
from email.parser import Parser
import supplier_lookup_handler
from PyPDF4 import PdfFileReader
from io import BytesIO
import tempfile
from datetime import datetime,timedelta

from PIL import Image
from io import BytesIO
import getOrgHandler
logger = logging.getLogger()

# TODO Move the business logic out of lambda handler
# SES event handler - no need to return
def handle(event, context):
    print(event)
    
    ses_event = event['Records'][0]['ses']
    getDestinationEmail=ses_event['mail']['destination']
    checkOrg=getOrgHandler.getOrgId(getDestinationEmail)
    print(checkOrg,'checkOrg')
    if not checkOrg:
        return 
    message_id = ses_event['mail']['messageId']
    from_email = ses_event['mail']['source']
    to_email = ses_event['receipt']['recipients'][0]
    alternateEmail=ses_event['mail']['commonHeaders']['from'][0]
    print(alternateEmail,'alternateEmail')
    validatesourceemail=is_valid_email(from_email)
    if validatesourceemail:
        pass
    else:


        validatealternateEmail=is_valid_email(alternateEmail)
        if validatealternateEmail:
            from_email=alternateEmail
        else:
            try:
                email_pattern = r'<([^>]+)>'
                match = re.search(email_pattern, alternateEmail)
                if match:
                    # Extract and print the email address
                    email_address = match.group(1)
                    print(email_address,'email_address')
                    from_email=email_address
                else:
                    print("No email address found in the input string.")
            except:
                pass
    print(from_email,'finalcheck')

    print(f'Message {message_id} sent from {from_email} to {to_email}')
    subjects=''
    emailreceviestime=''
    try:
        zulu_time_str=ses_event['mail']['timestamp']
        emailreceviestime = zulu_to_est(zulu_time_str)
        print("EST Time:", emailreceviestime)
    except Exception as e:
        logging.exception(e)

    try:
        getsubject=ses_event['mail']['headers']
        for sub in getsubject:
            if sub['name']=='Subject':
                print(sub['value'])
                subjects=sub['value']
            
    except Exception as e:
        logging.exception(e)
        pass
    
    from_username, from_domain = from_email.split('@')
    from_domainname = from_domain.split('.')[0]

    message_location = {'Bucket': utils.BUCKET_NAME, 'Key': message_id}
    document_directory = f'{from_domainname}/{from_username}_{from_domainname}/'
    print(f'Copying email message from bucket root ({utils.BUCKET_NAME}) to {document_directory}')

    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    s3_client.copy_object(
        CopySource = message_location,
        Bucket = utils.BUCKET_NAME,
        Key = f'{document_directory}{message_id}'
    )

    message_s3 = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key = f'{document_directory}{message_id}'
    )
    decoded_message = message_s3['Body'].read().decode('utf-8')
    parsed_message = Parser().parsestr(decoded_message)
    print('Processing email message recursively for extracting attachment and email body')
    
    document_list = []
    process_email_content(parsed_message, document_directory, document_list,to_email,subjects,from_email,emailreceviestime)
    print(f'Processed email documents: {document_list}')
    
    # Find supplier name from supplier email (invoice email sender)
    # supplier_name = supplier_lookup_handler.handle(from_email, to_email)
    
    #if no documents found handle exception and notify
    if not document_list:
        # errorMessage = 'No invoice attachment found, please check your email.'
        # utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '')
        # print(f'no attachment received from {from_email}')
        return 
    valid_ext=['.jpg','.jpeg','.png','.tiff','.pdf','.asc','.yxmd']   
    for document in document_list:
        docs_name=document.get("documentName")
        if document=={}:
            continue
        else:
            print(f'Triggering document analysis for {document.get("documentName")}')
            file_root, file_ext = os.path.splitext(document.get("documentName"))
            if file_ext.lower() not in valid_ext:
                errorMessage = 'Not valid document.'
                utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '',to_email)
                # utils.notify_backend_on_failure1(to_email, errorMessage, 'E0005', '',subjects,from_email,emailreceviestime)
                print(f'no attachment received from {from_email}')
                continue
            elif file_ext.lower()=='.pdf':
                document_checking=checkdocument(docs_name)
                if document_checking is True:
                    document.update({
                    'senderEmail': from_email,
                    'receiverEmail': to_email,
                    'vendorName': '',
                    'invoiceSource': 'Email',
                    'status': 'Processing'
                    })
                    print(document)
                    try:
                        start_document_analysis(document)
                    except Exception as e:
                        logging.exception(e)
                        utils.notify_backend_on_failure1(to_email, e, 'E0005', '',subjects,from_email,emailreceviestime)

                else:
                    errorMessage = 'Not valid document.'
                    utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '',to_email)
                    print(f'no attachment received from {from_email}')
                    document.update({
                    'senderEmail': from_email,
                    'receiverEmail': to_email,
                    'supplierName': '',
                    'invoiceSource': 'Email',
                    'status': 'Processing'
                    })
                    start_document_analysis(document)
            elif file_ext.lower()=='.jpg' or file_ext.lower()=='.jpeg' or file_ext.lower()=='.png' or file_ext.lower()=='.tiff':
                image_checking=image_file_check(docs_name)
                if image_checking==True:
                    document.update({
                    'senderEmail': from_email,
                    'receiverEmail': to_email,
                    'supplierName': '',
                    'invoiceSource': 'Email',
                    'status': 'Processing'
                    })
                    print(document)
                    try:
                        start_document_analysis(document)
                    except Exception as e:
                        logging.exception(e)
                        utils.notify_backend_on_failure1(to_email, e, 'E0005', '',subjects,from_email,emailreceviestime)

                else:
                    errorMessage = 'Not valid document.'
                    utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '',to_email)
                    print(f'no attachment received from {from_email}')
                    document.update({
                    'senderEmail': from_email,
                    'receiverEmail': to_email,
                    'supplierName': '',
                    'invoiceSource': 'Email',
                    'status': 'Processing'
                    })
                    try:
                        start_document_analysis(document)
                    except Exception as e:
                        logging.exception(e)
                        utils.notify_backend_on_failure1(to_email, e, 'E0005', '',subjects,from_email,emailreceviestime)



            elif file_ext.lower()==".asc" or file_ext.lower()==".yxmd":
                continue
                            
                
            else:
                errorMessage = 'Not valid document.'
                utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '',to_email)
                continue
                # document.update({
                # 'senderEmail': from_email,
                # 'receiverEmail': to_email,
                # 'supplierName': supplier_name,
                # 'invoiceSource': 'Email',
                # 'status': 'Initializing'
                # })
                # print(document)
                # start_document_analysis(document)

    return

'''
Process email message content and extracts each attached document
as an individual invoice along with email message body
'''
def process_email_content(message, document_directory, document_list,to_email,subjects,from_email,emailreceviestime):
    global message_body
    """
    If this is a multipart message, recursively iterate through each
    part, extracting all attachments and uploading each to a message-specific
    prefix within an attachments prefix.

    Based on example from:
    https://www.dev2qa.com/python-parse-emails-and-attachments-from-pop3-server-example/
    """

    content_type = message.get_content_type().lower()

    # if content_type == 'text/plain' or content_type == 'text/html':
    if content_type == 'text/plain':
        try:
            check=message.get('Content-Disposition')
            if not check:
                message_body = message.get_payload()
                print('message_body',message_body)
                try:
                    content_transfer_encoding = message.get('Content-Transfer-Encoding')
                    print(content_transfer_encoding,'content_transfer_encoding')
                    if content_transfer_encoding=='base64':
                        decoded_bytes = base64.b64decode(message_body)
                        message_body = decoded_bytes.decode("utf-8")
                except Exception as e:
                    logging.exception(e)            
                print(message_body,'message_body')
            else:
                errorMessage='Not valid document.'
                utils.notify_backend_on_failure(from_email, errorMessage, 'E0004', '',to_email)
        except Exception as e:
            logging.exception(e)
            message_body=''
           
    elif content_type.startswith('multipart'):
        body_msg_list = message.get_payload()
        for body_msg in body_msg_list:
            process_email_content(body_msg, document_directory, document_list,to_email,subjects,from_email,emailreceviestime)

    elif content_type.startswith('image') or content_type.startswith('application') or content_type=='text/csv' or content_type=='video/webm' or content_type=='audio/mpeg' or content_type=='text/html'and message.get('Content-Disposition') or content_type=='video/mp4'or content_type.startswith('video') or content_type.startswith('audio') or content_type=='text/comma-separated-values':
        try:
            attached_file_data = message.get_payload(decode=True)
        
            content_disposition = message.get('Content-Disposition')
            print(f'Content disposition {content_disposition}')
            
            attached_file_name = get_attachment_name(content_disposition)
            
        except Exception as e:
            logging.exception(e)
            attached_file_name=None
        # print(attached_file_name,'attached_file_nameattached_file_name')  
        # attached_file_name=None
        e='error'
        if  not attached_file_name:
            attachment_details={}
            print(to_email,'to_email')
            utils.notify_backend_on_failure1(to_email, e, 'E0005', '',subjects,from_email,emailreceviestime)
            document_list.append(attachment_details)
            
        else:
            # utils.notify_backend_on_failure('samiullah@apptomate.co', e, 'E0005', '')
            # document_list.append(attachment_details)
            
            spl_word=['.pdf','.jpeg','.jpg','.png','.tiff']
            for i in utils.file_extensions:
                if i in attached_file_name.lower():
                    print('true')
                    attached_file_name = attached_file_name.partition(i)[0]+attached_file_name.partition(i)[1]
                    print(attached_file_name,'attached_file_name')
                    break
                else:
                    print('false')
            print(f'Attachment file name {attached_file_name}')
            current_time= str(datetime.now())
            
            attached_file_name = encoded_words_to_text(attached_file_name)
            original_name=attached_file_name
            attached_file_name=f'{current_time}{attached_file_name}'
            print(f'Decoded attachment file name {attached_file_name}')
            attachment_file_path = f'{document_directory}{attached_file_name}'
            
            s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
            s3_client.put_object(
                Body = attached_file_data,
                Bucket = utils.BUCKET_NAME,
                Key = attachment_file_path,
            )
            message_body1=''
            try:
                if not message_body:
                    message_body=''
            except Exception as e:
                message_body=message_body1
                
    
            attachment_details = {
                'original_name':original_name,
                'fileName': attached_file_name,
                'folderName': document_directory,
                'documentName': attachment_file_path,
                'filepath': get_s3_file_path(attachment_file_path),
                'messageBody': message_body
                
            }
            docs_name_check = re.match(r'image\d+', original_name)
            docs_name_check_forinside_body = re.match(r'Untitled attachment', original_name)
            if docs_name_check is None:
                if docs_name_check_forinside_body is None:
                
                
                    document_list.append(attachment_details)
            else:
                attachment_details={}
                document_list.append(attachment_details)
        
def get_attachment_name(content_disposition):
    attachment_name_regex = r'(.*)filename=\"(.+)\"(.*)'
    if re.match(attachment_name_regex, content_disposition) is None:
        print('content_disposition',content_disposition.split('filename=')[1].strip('"'))
        return content_disposition.split('filename=')[1].strip('"')
    
    group1, group2, group3 = re.match(attachment_name_regex, content_disposition).groups()
    print(group1, group2, group3,'group1, group2, group3')
    return group2
    
def encoded_words_to_text(encoded_words):
    encoded_word_regex = r'=\?{1}(.+)\?{1}([b|q|B|Q])\?{1}(.+)\?{1}='
    if re.match(encoded_word_regex, encoded_words) is None:
        return encoded_words
    
    charset, encoding, encoded_text = re.match(encoded_word_regex, encoded_words).groups()
    print(f'Encoded attachment name {encoded_text}')
    byte_string = ''
    if encoding.upper() == 'B':
        byte_string = base64.b64decode(encoded_text)
    elif encoding.upper() == 'Q':
        byte_string = quopri.decodestring(encoded_text)
    return byte_string.decode(charset)


def get_s3_file_path(file_path):
    s3_file_path = f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/{file_path}'
    regex = r'(.jpg|.jpeg|.png|.tiff)';
    # s3_file_path = re.sub(regex, '.pdf', s3_file_path);
    return s3_file_path
    
    
# Starts document analysis by calling start-document-analysis-handler lambda
def start_document_analysis(event):
    lambda_client = boto3.client('lambda')
    analysis_response = lambda_client.invoke_async(
        # FunctionName='start-document-analysis-handler',
        FunctionName='FileUploadStep2-save-invoice-handler',
        InvokeArgs=json.dumps(event)
    )
    
def checkdocument(Keys):

    document_status=''
    client = boto3.client('s3')

    response=client.get_object(Bucket=utils.BUCKET_NAME,Key=Keys)

    data=response['Body'].read()
    # print(data)
    # pdf = PdfFileReader(BytesIO(data))
    # print(pdf)
    try:
        pdf = PdfFileReader(BytesIO(data))
        document_status=True

    except Exception as err:
        logging.exception( err)
        document_status=False
        pass
    print(document_status)
    return document_status



def image_file_check(src_document_name):
    imagefilecheck=''
    fileTemp = tempfile.NamedTemporaryFile(delete=False)

    s3_client = boto3.client('s3', region_name=utils.BUCKET_REGION)
    s3_client.download_fileobj(utils.BUCKET_NAME, src_document_name, fileTemp)
    fileTemp.close()

    print(fileTemp.name)

    try:
        img = Image.open(fileTemp.name)
        imagefilecheck=True
    except Exception as err:
        logging.exception( err)
        imagefilecheck=False
    finally:
        fileTemp.close()

    print(imagefilecheck)
    return imagefilecheck


def is_valid_email(email):
    # Regular expression for a basic email validation
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    
    # Use re.match to search for the pattern at the beginning of the string
    if re.match(pattern, email):
        return True
    else:
        return False
    

def zulu_to_est(zulu_time_str):
    # Convert Zulu time string to a datetime object
    zulu_time = datetime.strptime(zulu_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Calculate the time difference between UTC and EST (Eastern Standard Time)
    est_offset = timedelta(hours=-4)  # EST is 5 hours behind UTC

    # Convert Zulu time to EST time
    est_time = zulu_time + est_offset

    return est_time




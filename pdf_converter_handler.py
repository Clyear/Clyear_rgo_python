import os
import boto3
import utils
import logging
import tempfile

from PIL import Image
from io import BytesIO

logger = logging.getLogger()

# Private lambda - doesn't return http response
def handle(event, context):
    file_name = event.get('fileName')
    document_name = event.get('documentName')
    file_root, file_ext = os.path.splitext(file_name)
    
    # Convert to pdf
    if file_ext.lower() in utils.SUPPORTED_PDF_CONVERSIONS:
        pdf_document_name = document_name.replace(file_ext,'.pdf')
        pdf_file_name = file_name.replace(file_ext,'.pdf')
        try:
            print('Found image type, converting to pdf ', document_name, pdf_document_name)
            to_pdf(document_name, pdf_document_name)
            document_name = pdf_document_name
            file_name = pdf_file_name
        except Exception as error:
            print(f'Unable to convert document to pdf {str(error)}')
            utils.notify_backend_on_failure(event.get('senderEmail'), 'to convert document to pdf', 'E0002', document_name ,event.get('receiverEmail'))
            raise error

    # Return converted pdf file & document name
    return {
        'documentName': document_name,
        'fileName': file_name
    }

def to_pdf(src_document_name, dest_document_name):
    try:
        fileTemp = tempfile.NamedTemporaryFile(delete=False)

        s3_client = boto3.client('s3', region_name=utils.BUCKET_REGION)
        s3_client.download_fileobj(utils.BUCKET_NAME, src_document_name, fileTemp)
        fileTemp.close()
        
        print(fileTemp.name)
        
        img = Image.open(fileTemp.name)
        im = img.convert('RGB')
        
        in_mem_file = BytesIO()
        im.save(in_mem_file, format='pdf')
        in_mem_file.seek(0)
        
        
        s3_client.put_object(
            Body=in_mem_file,
            Bucket=utils.BUCKET_NAME,
            Key=dest_document_name
        )
        print('[ Converted PDF put to S3 ]', dest_document_name)

    except Exception as err:
        logging.exception(err)
        fileTemp.close()
    finally:
        fileTemp.close()
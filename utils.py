import os

# Environment variables
BUCKET_NAME = os.getenv('BUCKET_NAME')
BUCKET_REGION = os.getenv('BUCKET_REGION')
NODE_EXTRACTION_URL = os.getenv('NODE_EXTRACTION_URL')
ML_REST_URL = os.getenv('ML_REST_URL')
AUTH_HEADER = os.getenv('AUTH_HEADER')
OIS_BASIC_AUTH = (os.getenv('OIS_UNAME'), os.getenv('OIS_PWD'))

# Supportive constants
S3_HOME = f'https://{BUCKET_NAME}.s3.amazonaws.com/'
DEFAULT_VENDOR_NAME = 'N/A'
CUSTOMER_LOOKUP_SERVICE_TYPE = 'LOOKUP'

# Node V2 APIs
UPDATE_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/updateInvoice'
INVOICE_LINE_ITEMS_URL = f'{NODE_EXTRACTION_URL}/invoice/saveInvoiceExpenses'
FETCH_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceByJobId?expenseJobId='
SAVE_EXTRACTED_LABEL_URL = f'{NODE_EXTRACTION_URL}/invoice/saveExtractedLabels'
GET_VENDOR_LIST_URL = f'{NODE_EXTRACTION_URL}/invoice/getVendorList?customerId='
GET_CUSTOMER_ERP_URL = f'{NODE_EXTRACTION_URL}/invoice/getSubscriberERPDetails?customerId='
SAVE_EXPENSE_ITEM_URL = f'{NODE_EXTRACTION_URL}/invoice/saveInvoiceExpenses'
GET_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceById?invoiceId='


GET_TOUCH_LESS=f'{NODE_EXTRACTION_URL}/invoice/getTouchlessInvoiceById?invoiceId='
AUTO_APPROVAL=f'{NODE_EXTRACTION_URL}/invoice/autoApproval'

# Node V2 API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

# ML Rest APIs
DETECT_ENTITIES_URL = f'{ML_REST_URL}/live_detect_entities/'
IDENTIFY_SUPPLIER_URL = f'{ML_REST_URL}/supplier/unseen/'

# Supportive functions
def get_http_s3_path(text_json_path):
    return f'https://{BUCKET_NAME}.s3.amazonaws.com/{text_json_path}'


currencylist=['MXN','PHP','BRL','BZR']


currencylist1=['MXN','PHP','BRL','USD','EUR','GBP','CAD','INR','JPY','CHF','AUD','CNY','BZR','SEK','HKD']

taxKeyList=['tax total', 'total tax:', 'sales tax', 'tax', 'gst', 'taxes and surcharges', 'vat', 'gst tax', 'vat', 'taxamount', 'taxamount', 'tax', 'tax', 'gst', 'igst', 'tax amount', 'tax amount', 'taxes', 'taxes', 'taxes', 'taxation', 'taxation', 'taxation', 'tax-value', 'gst tax', 'gst tax', 'sales tax', 'sales tax amount', 'total tax', 'effective tax', 'effective tax amount', 'combined tax', 'taxrate', 'tax rate', 'tax rate', 'tax rate', 'tax rate', 'taxrate', 'taxrate', 'taxrate', 'tax percentage', 'taxpercentage', 'tax percentage', 'sales tax rate', 'average local tax rate', 'state tax rate', 'base tax rate', 'state vat', 'state sales tax', 'municipal tax rate', 'country tax rate', 'local sales tax', 'combined tax rate', 'total tax rate', 'effective tax rate', 'state tax', 'vat rate', 'vat%', 'sales tax($)', 'tax($)']
comparefieldobject=[{'awsTargetvariable':'INVOICE_RECEIPT_DATE','Clyear Target Varriable':'invoiceDate'},{'awsTargetvariable':'INVOICE_RECEIPT_ID','Clyear Target Varriable':'invoiceNumber'},{'awsTargetvariable':'ORDER_DATE','Clyear Target Varriable':'invoiceDate'},{'awsTargetvariable':'DUE_DATE','Clyear Target Varriable':'dueDate'},{'awsTargetvariable':'PO_NUMBER','Clyear Target Varriable':'orderNumber'},{'awsTargetvariable':'TOTAL','Clyear Target Varriable':'invoiceAmount'},{'awsTargetvariable':'AMOUNT_DUE','Clyear Target Varriable':'dueAmount'},{'awsTargetvariable':'SUBTOTAL','Clyear Target Varriable':'subTotal'}]      

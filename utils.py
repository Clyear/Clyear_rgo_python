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
FETCH_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceByJobId?analysisJobId='
SAVE_INVOICE_LABEL_URL = f'{NODE_EXTRACTION_URL}/invoice/saveExtractedLabels'
GET_VENDOR_LIST_URL = f'{NODE_EXTRACTION_URL}/invoice/getVendorList?customerId='
GET_CUSTOMER_ERP_URL = f'{NODE_EXTRACTION_URL}/invoice/getCustomerERPDetails?customerId='
GET_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceById?invoiceId='

# Node V2 API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}

# ML Rest APIs
DETECT_ENTITIES_URL = f'{ML_REST_URL}/live_detect_entities/'
IDENTIFY_SUPPLIER_URL = f'{ML_REST_URL}/vendor/unseen/'

# Supportive functions
def get_http_s3_path(text_json_path):
    return f'https://{BUCKET_NAME}.s3.amazonaws.com/{text_json_path}'


### default currency list

currencylist=['MXN','PHP','BRL']


currencylist1=['MXN','PHP','BRL','USD','EUR','GBP','CAD','INR','JPY','CHF','AUD','CNY','BZR','SEK','HKD','CA']





taxKeyList=['tax total', 'total tax:', 'sales tax', 'tax', 'taxes and surcharges', 'vat', 'vat', 'taxamount', 'taxamount', 'tax', 'tax',  'tax amount', 'tax amount', 'taxes', 'taxes', 'taxes', 'taxation', 'taxation', 'taxation', 'tax-value',  'sales tax', 'sales tax amount', 'total tax', 'effective tax', 'effective tax amount', 'combined tax', 'taxrate', 'tax rate', 'tax rate', 'tax rate', 'tax rate', 'taxrate', 'taxrate', 'taxrate', 'tax percentage', 'taxpercentage', 'tax percentage', 'sales tax rate', 'average local tax rate', 'state tax rate', 'base tax rate', 'state vat', 'state sales tax', 'municipal tax rate', 'country tax rate', 'local sales tax', 'combined tax rate', 'total tax rate', 'effective tax rate', 'state tax', 'vat rate', 'vat%', 'sales tax($)', 'tax($)']
gstlist=["gst",'gst tax','gst', 'igst','gst tax', 'gst tax']

pstlist=["pst",'PST']















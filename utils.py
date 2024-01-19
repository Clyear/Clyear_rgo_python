import os

# Environment variables
NODE_EXTRACTION_URL = os.getenv('NODE_EXTRACTION_URL')
AUTH_HEADER = os.getenv('AUTH_HEADER')

# Node APIs
GET_ENTITY_DATASET_URL = f'{NODE_EXTRACTION_URL}/invoice/getEntityTrainingDataset'
CREATE_DATASET_URL = f'{NODE_EXTRACTION_URL}/invoice/saveEntityTrainingDataset'
UPDATE_DATASET_URL = f'{NODE_EXTRACTION_URL}/invoice/updateEntityTrainingDataset'
GET_INVOICE_URL = f'{NODE_EXTRACTION_URL}/invoice/getInvoiceById?invoiceId='
FIND_VENDOR_URL = f'{NODE_EXTRACTION_URL}/invoice/getVendorDetails'
SAVE_VENDOR_URL = f'{NODE_EXTRACTION_URL}/invoice/saveVendorDetails'
UPDATE_VENDOR_URL = f'{NODE_EXTRACTION_URL}/invoice/updateVendorDetails'

INVOICE_ENTIITES = [
    'invoiceNumber',
    'dueDate',
    'dueAmount',
    'orderNumber',
    'invoiceDate',
    'invoiceCurrency',
    'invoiceDescription',
    'invoiceAmount',
    'taxTotal',
    'subTotal'
   
]
LINE_ITEM_ENTITIES = [
    'operatingUnit',
    'invoiceExpenseType',
    'invoiceLineNumber',
    'poNumber',
    'poLineNumber',
    'itemNumber',
    'itemDescription',
    'unitOfMeasure',
    'quantity',
    'unitPrice',
    'extendedPrice',
    'GLDate',
    'glAccount',
    'taxRate',
    'taxAmount'
    
]
STANDARD_FIELD_NAME=[
    'PRODUCT_CODE',
    'ITEM',
    'PRICE',
    'QUANTITY',
    'UNIT_PRICE',
    'EXPENSE_ROW',
    'OTHERS',
    'taxRate',
    'taxAmount'
    ] 


# Node API Header
API_V2_HEADER = {
    'authorization': AUTH_HEADER,
    'Content-Type': 'application/json'
}
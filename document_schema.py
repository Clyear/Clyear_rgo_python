from types import SimpleNamespace

class TDocumentSchema:
    document_metadata = SimpleNamespace(data_key='DocumentMetadata', type='object')
    blocks = SimpleNamespace(data_key='Blocks', type='list')
    analyze_document_model_version = SimpleNamespace(data_key='AnalyzeDocumentModelVersion')
    detect_document_text_model_version = SimpleNamespace(data_key='DetectDocumentTextModelVersion')
    status_message = SimpleNamespace(data_key='StatusMessage')
    warnings = SimpleNamespace(data_key='Warnings', type='object')
    job_status = SimpleNamespace(data_key='JobStatus')
    response_metadata = SimpleNamespace(data_key='ResponseMetadata', type='object')
    custom = SimpleNamespace(data_key='custom')
    next_token = SimpleNamespace(data_key='NextToken')

class TDocumentMetadataSchema:
    pages = SimpleNamespace(data_key="Pages")

class THttpHeadersSchema:
    date = SimpleNamespace(data_key="date")
    x_amzn_request_id = SimpleNamespace(data_key="x-amzn-requestid")
    content_type = SimpleNamespace(data_key="content-type")
    content_length = SimpleNamespace(data_key="content-length")
    connection = SimpleNamespace(data_key="connection")  

class TResponseMetadataSchema:
    request_id = SimpleNamespace(data_key='RequestId')
    http_status_code = SimpleNamespace(data_key="HTTPStatusCode")
    retry_attempts = SimpleNamespace(data_key="RetryAttempts")
    http_headers = SimpleNamespace(data_key="HTTPHeaders", type='object')

class TWarningsSchema:
    pages = SimpleNamespace(data_key="Pages", type='list')
    error_code = SimpleNamespace(data_key="ErrorCode")

class TBlockSchema:
    block_type = SimpleNamespace(data_key="BlockType")
    geometry = SimpleNamespace(data_key="Geometry", type="object")
    id = SimpleNamespace(data_key="Id")
    relationships = SimpleNamespace(data_key="Relationships", type='list')
    confidence = SimpleNamespace(data_key="Confidence")
    text = SimpleNamespace(data_key="Text")
    column_index = SimpleNamespace(data_key="ColumnIndex")
    column_span = SimpleNamespace(data_key="ColumnSpan")
    entity_types = SimpleNamespace(data_key="EntityTypes", type='list')
    page = SimpleNamespace(data_key="Page")
    row_index = SimpleNamespace(data_key="RowIndex")
    row_span = SimpleNamespace(data_key="RowSpan")
    selection_status = SimpleNamespace(data_key="SelectionStatus")
    text_type = SimpleNamespace(data_key="TextType")
    custom = SimpleNamespace(data_key="Custom")

class TRelationshipSchema:
    type = SimpleNamespace(data_key="Type")
    ids = SimpleNamespace(data_key="Ids", type="list")

class TGeometrySchema:
    bounding_box = SimpleNamespace(data_key="BoundingBox", type="object")
    polygon = SimpleNamespace(data_key="Polygon", type="list")

class TBoundingBoxSchema:
    width = SimpleNamespace(data_key="Width")
    height = SimpleNamespace(data_key="Height")
    left = SimpleNamespace(data_key="Left")
    top = SimpleNamespace(data_key="Top")

class TPointSchema:
    x = SimpleNamespace(data_key="X")
    y = SimpleNamespace(data_key="Y")
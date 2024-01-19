from enum import Enum, auto
from uuid import uuid4, UUID
from functools import lru_cache
from typing import List, Set, Optional
from dataclasses import dataclass, field, fields

import document_schema as schema

def load_data(instance, schema, **kwargs):
    for field in fields(type(instance)):
        field_name = field.name
        field_schema = getattr(schema, field_name, None)
        if field_schema is None:
            continue

        data_key=field_schema.data_key
        field_value = kwargs.get(data_key)
        if field_value is None:
            continue

        if hasattr(field_schema, 'type') and field_schema.type == 'object':
            field_instance = field.type(**field_value)
            setattr(instance, field_name, field_instance)
        elif hasattr(field_schema, 'type') and field_schema.type == 'list':
            if isinstance(field_value, list) and field_value != []:
                field_instance_list = []
                for item in field_value:
                    if field.type.__args__[0] not in [str]:
                        field_instance = field.type.__args__[0](**item)
                        field_instance_list.append(field_instance)
                    else:
                        field_instance_list = field_value
                        break
                setattr(instance, field_name, field_instance_list)
        else:
            setattr(instance, field_name, field_value)

class TextractBlockTypes(Enum):
    WORD = auto()
    LINE = auto()
    TABLE = auto()
    CELL = auto()
    KEY_VALUE_SET = auto()
    PAGE = auto()
    SELECTION_ELEMENT = auto()

@dataclass
class TextractEntityTypes(Enum):
    KEY = auto()
    VALUE = auto()

@dataclass(eq=True, repr=True)
class TDocumentMetadata():
    pages: int = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TDocumentMetadataSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TBoundingBox():
    width: float
    height: float
    left: float
    top: float

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TBoundingBoxSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TPoint():
    x: float
    y: float

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TPointSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TGeometry():
    bounding_box: TBoundingBox
    polygon: List[TPoint]

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TGeometrySchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TRelationship():
    type: str = field(default=None)
    ids: List[str] = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TRelationshipSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TBlock():
    geometry: TGeometry = field(default=None)
    id: str = field(default=None)
    block_type: str = field(default="")
    relationships: List[TRelationship] = field(default=None)
    confidence: float = field(default=None)
    text: str = field(default=None)
    column_index: int = field(default=None)
    column_span: int = field(default=None)
    entity_types: List[str] = field(default=None)
    page: int = field(default=None)
    row_index: int = field(default=None)
    row_span: int = field(default=None)
    selection_status: str = field(default=None)
    text_type: str = field(default=None)
    custom: dict = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TBlockSchema,
            **kwargs
        )

    def __hash__(self) -> int:
        return hash(self.id)    

    def get_relationships_for_type(self, relationship_type="CHILD") -> Optional[TRelationship]:
        """assuming only one relationship type entry in the list"""
        if self.relationships:
            for r in self.relationships:
                if r.type == relationship_type:
                    return r
        return None

@dataclass(eq=True, repr=True)
class TWarnings():
    error_code: str = field(default=None)
    pages: List[int] = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TWarningsSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class THttpHeaders():
    x_amzn_request_id: str = field(default=None)
    content_type: str = field(default=None)
    content_length: int = field(default=None)
    connection: str = field(default=None)
    date: str = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.THttpHeadersSchema,
            **kwargs
        )

@dataclass(eq=True, repr=True)
class TResponseMetadata():
    request_id: str = field(default=None)
    http_status_code: int = field(default=None)
    retry_attempts: int = field(default=None)
    http_headers: THttpHeaders = field(default=None)

    def __init__(self, **kwargs):
        load_data(
            instance = self,
            schema = schema.TResponseMetadataSchema,
            **kwargs
        )

@dataclass(eq=True, init=True, repr=True)
class TDocument():
    document_metadata: TDocumentMetadata = field(default=None)
    blocks: List[TBlock] = field(default=None)
    analyze_document_model_version: str = field(default=None)
    detect_document_text_model_version: str = field(default=None)
    status_message: str = field(default=None)
    warnings: TWarnings = field(default=None)
    job_status: str = field(default=None)
    response_metadata: TResponseMetadata = field(default=None)
    custom: dict = field(default=None)
    next_token: str = field(default=None)
    id: UUID = field(default_factory=uuid4)

    def __init__(self, **kwargs):
        self.id = uuid4()
        load_data(
            instance = self,
            schema = schema.TDocumentSchema,
            **kwargs
        )

    def __hash__(self):
        return int(self.id)

    def get_block_by_id(self, id: str) -> TBlock:
        for block in self.blocks:
            if block.id == id:
                return block
        raise ValueError(f"no block for id: {id}")

    def __relationships_recursive(self, block: TBlock) -> List[TBlock]:
        import itertools
        if block and block.relationships:
            all_relations = list(itertools.chain(*[r.ids for r in block.relationships if r and r.ids]))
            all_block = [self.get_block_by_id(id) for id in all_relations if id]
            for b in all_block:
                if b:
                    yield b
                    for child in self.__relationships_recursive(block=b):
                        yield child

    @lru_cache()
    def relationships_recursive(self, block: TBlock) -> Set[TBlock]:
        return set(self.__relationships_recursive(block=block))
    
    @staticmethod
    def filter_blocks_by_type(block_list: List[TBlock], textract_block_type: List[TextractBlockTypes] = None) -> List[TBlock]:
        if textract_block_type:
            block_type_names = [x.name for x in textract_block_type]
            return [b for b in block_list if b.block_type in block_type_names]
        else:
            return list()

    def get_blocks_by_type(self, block_type_enum: TextractBlockTypes = None, page: TBlock = None) -> List[TBlock]:
        table_list: List[TBlock] = list()
        if page and page.relationships:
            block_list = list(self.relationships_recursive(page))
            if block_type_enum:
                return self.filter_blocks_by_type(block_list=block_list, textract_block_type=[block_type_enum])
            else:
                return block_list
        else:
            if self.blocks:
                for b in self.blocks:
                    if block_type_enum and b.block_type == block_type_enum.name:
                        table_list.append(b)
                return table_list
            else:
                return list()

    def pages(self) -> List[TBlock]:
        return self.get_blocks_by_type(block_type_enum=TextractBlockTypes.PAGE)

    def lines(self, page: TBlock) -> List[TBlock]:
        return self.get_blocks_by_type(page=page, block_type_enum=TextractBlockTypes.LINE)            

    def forms(self, page: TBlock) -> List[TBlock]:
        return self.get_blocks_by_type(page=page, block_type_enum=TextractBlockTypes.KEY_VALUE_SET)

    def keys(self, page: TBlock) -> List[TBlock]:
        for key_entities in self.forms(page=page):
            if TextractEntityTypes.KEY.name in key_entities.entity_types:
                yield key_entities
        
    def get_blocks_for_relationships(self, relationship: TRelationship = None) -> List[TBlock]:
        all_blocks: List[TBlock] = list()
        if relationship and relationship.ids:
            for id in relationship.ids:
                all_blocks.append(self.get_block_by_id(id))
        return all_blocks

    def child_for_key(self, key: TBlock) -> List[TBlock]:
        return_value_for_key: List[TBlock] = list()
        if TextractEntityTypes.KEY.name in key.entity_types:
            if key and key.relationships:
                value_blocks = self.get_blocks_for_relationships(relationship=key.get_relationships_for_type())
                return value_blocks

        return return_value_for_key

    def value_for_key(self, key: TBlock) -> List[TBlock]:
        return_value_for_key: List[TBlock] = list()
        if TextractEntityTypes.KEY.name in key.entity_types:
            if key and key.relationships:
                value_blocks = self.get_blocks_for_relationships(relationship=key.get_relationships_for_type("VALUE"))
                for block in value_blocks:
                    return_value_for_key.extend(self.get_blocks_for_relationships(block.get_relationships_for_type()))

        return return_value_for_key

    @staticmethod
    def get_text_for_tblocks(tblocks: List[TBlock]) -> str:
        return_value = ' '.join([x.text for x in tblocks if x and x.text])
        return_value += ' '.join([x.selection_status for x in tblocks if x and x.selection_status])
        return return_value

    def form_values(self, pages: List[TBlock]):
        key_entities = []
        for page in pages:
            key_entities.extend(self.keys(page))

        form_values = {}
        for key_entity in key_entities:
            key_word_blocks = self.child_for_key(key_entity)
            key_text = TDocument.get_text_for_tblocks(key_word_blocks)
            
            value_for_key = self.value_for_key(key_entity)
            value_text = TDocument.get_text_for_tblocks(value_for_key)
            
            existing_value_text = form_values.get(key_text, '')
            if len(existing_value_text) > len(value_text):
                continue
            
            form_values[key_text] = value_text
        return form_values

    def content(self, pages: List[TBlock]):
        content = ''
        for page_block in pages:
            lines = self.lines(page_block)
            line_text = TDocument.get_text_for_tblocks(lines)
            content += f'{line_text} '
        return content.strip()


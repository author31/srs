import httpx
from app.database import get_db_session
from app.services import config_service

from typing import List, Optional, Any, Union, Literal
from datetime import datetime
from pydantic import BaseModel, HttpUrl, ValidationError


NOTION_BASE_URL = "https://api.notion.com/v1"
SEARCH_ENDPOINT = NOTION_BASE_URL + "/search"

class UserRef(BaseModel):
    object: Literal['user']
    id: str

class ExternalFile(BaseModel):
    url: HttpUrl

class Parent(BaseModel):
    type: Literal['database_id']
    database_id: str

# Page Model
class Page(BaseModel):
    object: Literal['page']
    id: str
    created_time: datetime
    last_edited_time: datetime
    created_by: UserRef
    last_edited_by: UserRef
    cover: dict
    icon: dict
    parent: Parent
    archived: bool
    properties: dict
    url: HttpUrl

# Success Response
class ListResponse(BaseModel):
    object: Literal['list']
    results: List[Page]
    next_cursor: Optional[Any]
    has_more: bool
    type: Literal['page_or_database']
    page_or_database: dict[Any, Any]

# Error Response
class ErrorResponse(BaseModel):
    object: Literal['error']
    status: int
    code: str
    message: str

NotionResponse = Union[ListResponse, ErrorResponse]


### SERVICES

def construct_headers():
    db = get_db_session()
    api_key = config_service.get_config_value(db, "notion_api_key")
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

def query_notion_database(
    database_id: str,
    payload: Optional[dict] = None,
    timeout: float = 10.0,
    headers = construct_headers(),
) -> NotionResponse:
    """
    Query a Notion database and return a parsed Pydantic response.

    :param api_key:        Your Notion integration token.
    :param database_id:   The Notion database ID to query.
    :param payload:       Optional JSON body to send (e.g. filters, sorts).
    :param timeout:       Request timeout in seconds.
    :return:              Either ListResponse on 200, or ErrorResponse on 400/429.
    """
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    try:
        resp = httpx.post(url, json=payload or {}, headers=headers, timeout=timeout)
    except httpx.RequestError as e:
        # network-level errors
        return ErrorResponse(
            object="error",
            status=0,
            code="request_error",
            message=str(e),
        )

    # parse known error cases explicitly
    if resp.status_code == 429:
        return ErrorResponse(**resp.json())
    if resp.status_code == 400:
        return ErrorResponse(**resp.json())

    # for any other HTTP error, raise or wrap
    resp.raise_for_status()

    # at 200, parse into ListResponse
    try:
        return ListResponse(**resp.json())
    except ValidationError as ve:
        # if it somehow doesn't match the schema
        return ErrorResponse(
            object="error",
            status=500,
            code="validation_error",
            message=str(ve),
        )

def retrieve_content_by_id(page_id, headers=construct_headers()):
    """
    sample curl: 
    curl 'https://api.notion.com/v1/pages/b55c9c91-384d-452b-81db-d1ef79372b75' \
      -H 'Notion-Version: 2022-06-28' \
      -H 'Authorization: Bearer '"$NOTION_API_KEY"''
    """
    pass

def update_page_properties_by_id(page_id, headers=construct_headers()):
    """
    sample curl:
    curl https://api.notion.com/v1/pages/60bdc8bd-3880-44b8-a9cd-8a145b3ffbd7 \
      -H 'Authorization: Bearer '"$NOTION_API_KEY"'' \
      -H "Content-Type: application/json" \
      -H "Notion-Version: 2022-06-28" \
      -X PATCH \
        --data '{
      "properties": {
        "In stock": { "checkbox": true }
      }
    }'
    """

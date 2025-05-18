import json
import logging

import httpx
from pydantic import ValidationError
from app.knowledge_sources import notion
from app.knowledge_sources.notion import schemas
from app.exceptions import SRSException

logger = logging.getLogger(__name__)

TIMEOUT = 10.0
NOTION_BASE_URL = "https://api.notion.com/v1"

def construct_headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

async def fetch_api(url: str, method: str, api_key: str,
                    payload: dict | None = None, params: dict | None = None, timeout: float = TIMEOUT) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(url=url, method=method, json=payload or None, params=params or None, headers=construct_headers(api_key))
    except httpx.RequestError as e:
        # network-level errors
        raise SRSException(code="network_error", message=str(e))

    # any non-2xx status is an error
    if not (200 <= resp.status_code < 300):
        # try to extract code/message from body
        text = resp.text or ""
        try:
            body = resp.json()
            code = body.get("code", f"HTTP_{resp.status_code}")
            message = body.get("message", text)
        except (ValueError, json.JSONDecodeError):
            code = f"HTTP_{resp.status_code}"
            message = text
        raise SRSException(code=code, message=message)

     # parse 2xx JSON
    try:
        return resp.json()
    except (ValueError, json.JSONDecodeError) as e:
        raise SRSException(code="invalid_json", message=str(e))

async def query_notion_database(
    database_id: str,
    api_key: str,
    payload: dict | None = None,
) -> schemas.NotionDatabaseQueryData | None:
    """
    tobefilled
    """
    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"
    try:
        response =  await fetch_api(url=url, method="post", api_key=api_key, payload=payload)
        return schemas.NotionDatabaseQueryData(**response)
    except SRSException as e:
        logger.error(f"Notion fetch children failed [{e.code}]: {e.message}")
        return None


async def fetch_flashcard_db(page_id: str, api_key: str) -> list[schemas.Flashcard] | None:
    """
    tobefilled
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    try:
        response = await fetch_api(url=url, method="GET", api_key=api_key)
        block_children_data = schemas.NotionBlockChildrenData(**response)
    except SRSException as e:
        logger.error(f"Notion fetch db failed [{e.code}]: {e.message}")
        return None

    flashcard_child_db = list(filter(lambda x: hasattr(x, "child_database"), block_children_data.items))
    if not flashcard_child_db:
        return None

    if len(flashcard_child_db)>1:
        logger.warning("NotionTemplateError: There are more than 1 flashcard database, Getting the first database.")

    if isinstance(flashcard_child_db, list):
        flashcard_child_db = flashcard_child_db[0]

    notion_db_query_data = await query_notion_database(database_id=flashcard_child_db.id, api_key=api_key)
    if not notion_db_query_data:
        return None

    flashcards = [
        schemas.Flashcard(**item.properties)
        for item in notion_db_query_data.items
    ]

    return flashcards


def update_page_properties_by_id(page_id, headers):
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

async def fetch_flashcards(database_id: str, api_key: str):
    payload={
        "filter": {
          "property": "isProcessed",
          "checkbox": {
            "equals": False
          }
        }
    }

    result = await query_notion_database(database_id=database_id, payload=payload, api_key=api_key)
    if result.status != 200:
        logger.error(f"Error raised while fetching: {result.message}")
        return

    if isinstance(result, schemas.ListResponse):
        logger.info(f"Fetched {len(result.items)} from Notion.")
        for page in result.items:
            print(page)


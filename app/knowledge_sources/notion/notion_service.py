import json
import logging
import httpx
from pydantic import ValidationError

from app.database import get_db_session
from app.knowledge_sources.notion import schemas
from app.services import config_service

logger = logging.getLogger(__name__)

NOTION_BASE_URL = "https://api.notion.com/v1"
SEARCH_ENDPOINT = NOTION_BASE_URL + "/search"

def construct_headers():
    db = get_db_session()
    api_key = config_service.get_config_value(db, "notion_api_key")
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

async def query_notion_database(
    database_id: str,
    payload: dict | None = None,
    timeout: float = 10.0,
    headers = construct_headers(),
) -> schemas.NotionResponse:
    """
    Query a Notion database and return a parsed Pydantic response.

    :param database_id:   The Notion database ID to query.
    :param payload:       Optional JSON body to send (e.g. filters, sorts).
    :param timeout:       Request timeout in seconds.
    :return:              Either ListResponse on 200, or ErrorResponse on 400/429.
    """
    url = f"{NOTION_BASE_URL}/databases/{database_id}/query"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload or {}, headers=headers, timeout=timeout)
    except httpx.RequestError as e:
        # network-level errors
        return schemas.ErrorResponse(
            object="error",
            status=0,
            code="request_error",
            message=str(e),
        )

    # parse known error cases explicitly
    if resp.status_code == 429:
        return schemas.ErrorResponse(**resp.json())
    if resp.status_code == 400:
        return schemas.ErrorResponse(**resp.json())

    # for any other HTTP error, raise or wrap
    resp.raise_for_status()

    # at 200, parse into ListResponse
    try:
        return schemas.ListResponse(**resp.json())
    except ValidationError as ve:
        # if it somehow doesn't match the schema
        return schemas.ErrorResponse(
            object="error",
            status=500,
            code="validation_error",
            message=str(ve),
        )

async def fetch_all_blocks_recursive(block_id: str, headers: dict = construct_headers()):
    """
    Recursively fetches all blocks starting from a given block ID.
    If a block has children, it fetches them and adds them under a 'children' key.
    """
    all_children= []
    start_cursor= None
    url = f"{NOTION_BASE_URL}/blocks/{block_id}/children"
    async with httpx.AsyncClient() as client:
        while True:
            params = {}
            if start_cursor:
                params["start_cursor"] = start_cursor

            try:
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                all_children.extend(results)

                if not data.get("has_more"): break 

                start_cursor = data.get("next_cursor")

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                break
            except httpx.RequestError as e:
                logger.error(f"Request error occurred: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                break

    processed_children = []
    for child_block in all_children:
        if child_block.get("has_more"): 
            nested_children = await fetch_all_blocks_recursive(child_block["id"], headers)
            child_block["children"] = nested_children
            processed_children.append(child_block)
            continue

        processed_children.append(child_block)

    return processed_children

async def retrieve_content_by_id(page_id, headers=construct_headers()):
    """
    Fetches all blocks for a given Notion Page ID recursively.

    Args:
        page_id: The UUID of the Notion page.
        api_key: Optional Notion API key. If None, reads from NOTION_API_KEY env var.

    Returns:
        A dictionary representing the PageContent, containing the page_id
        and a list of top-level blocks with nested children.
        Returns an empty structure on failure.
    """
    try:
        top_level_blocks = await fetch_all_blocks_recursive(page_id, headers)

        page_content = {
            "page_id": page_id,
            "blocks": top_level_blocks,
        }
        return page_content

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {"page_id": page_id, "blocks": [], "error": str(e)}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {"page_id": page_id, "blocks": [], "error": f"Unexpected error: {e}"}


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


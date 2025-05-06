import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.knowledge_sources.notion import notion_service
from app.services import config_service

logger = logging.getLogger(__name__)

async def fetch_from_notion(db: Session) -> dict[str, Any]:
    """
    Fetch data from Notion based on the configured database ID.

    Args:
        db: Database session

    Returns:
        Dict containing fetched results or error information
    """
    try:
        notion_api_key = config_service.get_config_value(db, "notion_api_key")
        notion_database_id = config_service.get_config_value(db, "notion_database_id")

        if not notion_api_key:
            return {"status": "error", "message": "Notion API key not configured"}

        if not notion_database_id:
            return {"status": "error", "message": "Notion database ID not configured"}

        payload={
            "filter": {
              "property": "isProcessed",
              "checkbox": {
                "equals": False
              }
            }
        }

        response = await notion_service.query_notion_database(database_id=notion_database_id, payload=payload)

        if hasattr(response, "object") and response.object == "error":
            return {
                "status": "error",
                "message": f"Notion API error: {response.message}",
                "code": response.code
            }

        # For each page in results, get its content
        pages_content = []
        for page in response.results[:5]:  # Limit to 5 pages to avoid rate limits
            page_id = page.id
            page_url = page.url
            page_title = extract_page_title(page.properties)

            # Fetch blocks for this page
            content = await notion_service.retrieve_content_by_id(page_id)

            # Extract text content from blocks for preview
            preview_text = extract_preview_text(content.get("blocks", []))

            pages_content.append({
                "id": page_id,
                "url": page_url,
                "title": page_title,
                "preview": preview_text[:300] + "..." if len(preview_text) > 300 else preview_text,
                "full_content": content
            })

        return {
            "status": "success",
            "source": "notion",
            "pages": pages_content,
            "total_count": len(response.results),
            "fetched_count": len(pages_content)
        }

    except Exception as e:
        logger.error(f"Error fetching from Notion: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Error fetching from Notion: {str(e)}"}

def extract_page_title(properties: dict) -> str:
    """Extract a title from page properties"""
    # Try common property names for titles
    title_candidates = ["Name", "Title", "name", "title"]

    for candidate in title_candidates:
        if candidate in properties:
            prop = properties[candidate]
            if "title" in prop and prop["title"]:
                title_parts = [text_obj.get("plain_text", "") for text_obj in prop["title"]]
                return " ".join(title_parts)

    return "Untitled Page"

def extract_preview_text(blocks: list[dict]) -> str:
    """Extract plain text from blocks for preview purposes"""
    texts = []

    for block in blocks[:10]:  # Limit to first 10 blocks
        block_type = block.get("type")

        if block_type == "paragraph":
            paragraph = block.get("paragraph", {})
            rich_text = paragraph.get("rich_text", [])
            for text_obj in rich_text:
                texts.append(text_obj.get("plain_text", ""))

        elif block_type == "heading_1" or block_type == "heading_2" or block_type == "heading_3":
            heading = block.get(block_type, {})
            rich_text = heading.get("rich_text", [])
            for text_obj in rich_text:
                texts.append(text_obj.get("plain_text", ""))

    return " ".join(texts)

async def fetch_from_all_sources(db: Session) -> dict[str, Any]:
    """
    Fetch data from all configured knowledge sources.
    Currently only supports Notion, but designed to be extended.

    Args:
        db: Database session

    Returns:
        Dict containing all fetched results
    """
    results = {
        "sources": [],
        "overall_status": "success"
    }

    # Fetch from Notion
    notion_results = await fetch_from_notion(db)
    if notion_results["status"] == "success":
        results["sources"].append({
            "name": "Notion",
            "status": "success",
            "data": notion_results
        })
    else:
        results["sources"].append({
            "name": "Notion",
            "status": "error",
            "error": notion_results["message"]
        })
        results["overall_status"] = "partial"

    return results

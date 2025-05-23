import logging
import os

import pytest

from app.knowledge_sources.notion import notion_service
from app.services.config_service import get_config_value, set_config_value
from tests.conftest import (
    db_session,
    init_db_tables,
    notion_test_config,
    override_get_db_session,
)

# Set up DEBUG flag from environment variable
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TestNotionService:

    @pytest.mark.asyncio
    async def test_set_config_value_inserts_api_key(self, init_db_tables, db_session, notion_test_config):
        """
        Test that the API key can be inserted into the SQLite database.
        """
        api_key = notion_test_config["api_key"]
        set_config_value(db_session, "notion_api_key", api_key)
        db_session.commit()  # Ensure it's committed

        # Retrieve and verify
        retrieved_key = get_config_value(db_session, "notion_api_key")
        assert retrieved_key == api_key, "API key was not correctly inserted into the database"

        if DEBUG:
            logger.info(f"Inserted and retrieved API key: {retrieved_key}")

    @pytest.mark.asyncio
    async def test_query_notion_database_success(self, db_session, notion_test_config):
        """
        Test successful querying of Notion database with real HTTP response.
        """
        database_id = notion_test_config["database_id"]  # Use the test page ID from config
        payload = {}  # Example payload
        headers = notion_service.construct_headers()  # This will use the real API key
        result = await notion_service.query_notion_database(database_id, payload, headers=headers)

        if DEBUG:
            logger.info(f"Response from query_notion_database: {result}")

        assert result.object == "list", "Expected a list response from Notion API"

    @pytest.mark.asyncio
    async def test_query_notion_database_error(self, db_session):
        """
        Test error handling in query_notion_database with a potentially invalid input.
        """
        invalid_database_id = "invalid_database_id"  # This should trigger an error
        result = await notion_service.query_notion_database(invalid_database_id, None)

        if DEBUG:
            logger.info(f"Error response from query_notion_database: {result}")

        assert result.object == "error", "Expected an error response from Notion API"

    @pytest.mark.asyncio
    async def test_fetch_all_blocks_recursive_success(self, db_session, notion_test_config):
        """
        Test successful recursive fetching of blocks with real HTTP responses.
        """
        block_id = notion_test_config["page_id"] 
        headers = notion_test_config["headers"] 
        result = await notion_service.fetch_all_blocks_recursive(block_id, headers=headers)

        if DEBUG:
            logger.info(f"Response from fetch_all_blocks_recursive: {result}")

        assert isinstance(result, list), "Expected a list of blocks"
        assert len(result) > 0, "At least one block should be returned from Notion API"

    @pytest.mark.asyncio
    async def test_retrieve_content_by_id_success(self, db_session, notion_test_config):
        """
        Test successful retrieval of content by ID with real HTTP response.
        """
        page_id = notion_test_config["page_id"]  # Use the test page ID from config
        headers = notion_test_config["headers"]  # Real headers with API key
        result = await notion_service.retrieve_content_by_id(page_id, headers=headers)

        if DEBUG:
            logger.info(f"Response from retrieve_content_by_id: {result}")

        assert result is not None, "Expected content to be retrieved"
        assert "blocks" in result, "Expected a Notion API response object"

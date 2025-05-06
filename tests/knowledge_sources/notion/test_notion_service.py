import os
import logging
import pytest
from app.knowledge_sources.notion.service import query_notion_database, fetch_all_blocks_recursive, construct_headers
from app.services.config_service import set_config_value, get_config_value

# Set up DEBUG flag from environment variable
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
logger = logging.getLogger(__name__)

# Use fixtures from conftest.py
@pytest.mark.usefixtures("db_session", "notion_test_config", "override_get_db_session")
@pytest.mark.integration
class TestNotionService:

    def test_set_config_value_inserts_api_key(self, db_session, notion_test_config):
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

    @pytest.mark.integration
    def test_query_notion_database_success(self, db_session, notion_test_config):
        """
        Test successful querying of Notion database with real HTTP response.
        """
        database_id = notion_test_config["page_id"]  # Use the test page ID from config
        payload = {}  # Example payload
        headers = construct_headers()  # This will use the real API key
        result = query_notion_database(database_id, payload, headers=headers)

        if DEBUG:
            logger.info(f"Response from query_notion_database: {result}")

        assert result.object == "list", "Expected a list response from Notion API"

    @pytest.mark.integration
    def test_query_notion_database_error(self, db_session):
        """
        Test error handling in query_notion_database with a potentially invalid input.
        """
        invalid_database_id = "invalid_database_id"  # This should trigger an error
        result = query_notion_database(invalid_database_id, None)

        if DEBUG:
            logger.info(f"Error response from query_notion_database: {result}")

        assert result.object == "error", "Expected an error response from Notion API"

    @pytest.mark.integration
    def test_fetch_all_blocks_recursive_success(self, db_session, notion_test_config):
        """
        Test successful recursive fetching of blocks with real HTTP responses.
        """
        block_id = notion_test_config["page_id"]  # Use the test page ID
        headers = notion_test_config["headers"]  # Real headers with API key
        result = fetch_all_blocks_recursive(block_id, headers=headers)

        if DEBUG:
            logger.info(f"Response from fetch_all_blocks_recursive: {result}")

        assert isinstance(result, list), "Expected a list of blocks"
        assert len(result) > 0, "At least one block should be returned from Notion API"

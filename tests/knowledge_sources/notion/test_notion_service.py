import pytest
from unittest.mock import patch
import httpx
from app.knowledge_sources.notion.service import query_notion_database, fetch_all_blocks_recursive, construct_headers
from app.services.config_service import set_config_value

# Use fixtures from conftest.py
@pytest.mark.usefixtures("db_session", "notion_test_config", "override_get_db_session")
class TestNotionService:

    def test_set_config_value_inserts_api_key(self, db_session, notion_test_config):
        """
        Test that the API key can be inserted into the SQLite database.
        """
        api_key = notion_test_config["api_key"]
        set_config_value(db_session, "notion_api_key", api_key)
        db_session.commit()  # Ensure it's committed

        # Retrieve and verify
        from app.services.config_service import get_config_value
        retrieved_key = get_config_value(db_session, "notion_api_key")
        assert retrieved_key == api_key, "API key was not correctly inserted into the database"

    @patch("httpx.post")
    def test_query_notion_database_success(self, mock_post, db_session, notion_test_config):
        """
        Test successful querying of Notion database with mocked HTTP response.
        """
        mock_response = httpx.Response(200, json={"object": "list", "results": []})
        mock_post.return_value = mock_response

        payload = {}  # Example payload
        database_id = "test_database_id"  # Use a test ID
        result = query_notion_database(database_id, payload, headers=construct_headers())

        assert result.object == "list", "Expected a list response"
        mock_post.assert_called_once()  # Ensure the HTTP call was made

    @patch("httpx.post")
    def test_query_notion_database_error(self, mock_post, db_session):
        """
        Test error handling in query_notion_database, e.g., for a 400 error.
        """
        mock_error_response = httpx.Response(400, json={"object": "error", "status": 400, "code": "validation_error"})
        mock_post.return_value = mock_error_response

        result = query_notion_database("invalid_database_id", None)

        assert result.object == "error", "Expected an error response"
        assert result.status == 400, "Error status code should match"

    @patch("httpx.get")
    def test_fetch_all_blocks_recursive_success(self, mock_get, db_session, notion_test_config):
        """
        Test successful recursive fetching of blocks with mocked HTTP responses.
        """
        mock_response = httpx.Response(200, json={"object": "list", "results": [{"id": "block1", "has_children": False}]})
        mock_get.return_value = mock_response

        block_id = "test_block_id"
        result = fetch_all_blocks_recursive(block_id, headers=notion_test_config["headers"])

        assert isinstance(result, list), "Expected a list of blocks"
        assert len(result) > 0, "At least one block should be returned"
        mock_get.assert_called()  # Ensure the HTTP call was attempted

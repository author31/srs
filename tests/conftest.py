import logging
import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.models import Base

load_dotenv(dotenv_path=".env.integration.test")

TEST_DATABASE_URL = "sqlite:///.local/test_flashcards.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def init_db_tables():
    Base.metadata.create_all(test_engine)
    yield

# Fixture to provide a test database session
@pytest.fixture(scope="function")
def db_session():
    """Provides a clean transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# Fixture to override the app's db session getter
@pytest.fixture(autouse=True)
def override_get_db_session(monkeypatch, db_session):
    """
    Monkeypatches the application's get_db_session to use the
    test database session for the duration of a test.
    """
    def mock_get_db_session():
        return db_session  # Return the managed session

    try:
        monkeypatch.setattr("app.knowledge_sources.notion.notion_service.get_db_session", mock_get_db_session)
    except AttributeError:
        logging.warning("Warning: Could not patch get_db_session in app.knowledge_sources.notion.service.")

    try:
        monkeypatch.setattr("app.services.config_service.get_db_session", mock_get_db_session)
    except AttributeError:
        logging.warning("Warning: Could not patch get_db_session in app.services.config_service.")

# Fixture to load Notion API key and other test IDs
@pytest.fixture(scope="session")
def notion_test_config():
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("TEST_NOTION_DATABASE_ID")

    if not all([api_key, database_id]):
        pytest.skip("Skipping Notion integration tests: Required environment variables (.env.integration.test) not set.", allow_module_level=True)

    return {
        "api_key": api_key,
        "page_id": database_id,
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    }

# Fixture to ensure the API key is in the test DB before tests run
@pytest.fixture(scope="function", autouse=True)
def setup_notion_config_in_db(db_session: Session, notion_test_config):
    """Inserts the Notion API key into the test database."""
    from app.services import config_service  # Import locally to use patched DB

    try:
        config_service.set_config_value(db_session, "notion_api_key", notion_test_config["api_key"])
        db_session.commit()  # Commit the change
    except AttributeError as e:
        logging.error(f"Error setting config value: {e}")
        pytest.skip("Skipping tests: config_service.set_config_value is not available.")
    except Exception as e:
        logging.error(f"Unexpected error setting up config: {e}")
        pytest.fail("Failed to set up test configuration.")

def pytest_configure(config):
    """
    Configure pytest-asyncio to explicitly set the default event loop scope.
    This avoids warnings and ensures compatibility with future versions.
    """
    config.option.asyncio_default_fixture_loop_scope = "function"  # Set to "function" scope


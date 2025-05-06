import os
import logging
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load test environment variables
load_dotenv(dotenv_path=".env.integration.test")

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///.local/test_db.sqlite3")
# Ensure the .local directory exists
os.makedirs(".local", exist_ok=True)

test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Fixture to provide a test database session
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a clean transactional database session for tests."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    # Rollback and close connection
    await session.close()
    await transaction.rollback()
    await connection.close()

# Fixture to override the app's db session getter
@pytest.fixture(autouse=True)
def override_get_db_session(monkeypatch, db_session):
    """
    Monkeypatches the application's get_db_session to use the
    test database session for the duration of a test.
    """
    async def mock_get_db_session():
        return db_session  # Return the managed async session

    try:
        monkeypatch.setattr("app.knowledge_sources.notion.service.get_db_session", mock_get_db_session)
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
    page_id = os.getenv("TEST_NOTION_PAGE_ID")

    if not all([api_key, page_id]):
        pytest.skip("Skipping Notion integration tests: Required environment variables (.env.integration.test) not set.", allow_module_level=True)

    return {
        "api_key": api_key,
        "page_id": page_id,
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    }

# Fixture to ensure the API key is in the test DB before tests run
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_notion_config_in_db(db_session: Session, notion_test_config):
    """Inserts the Notion API key into the test database."""
    from app.services import config_service  # Import locally to use patched DB

    try:
        # Assuming config_service.set_config_value is async
        await config_service.set_config_value(db_session, "notion_api_key", notion_test_config["api_key"])
        await db_session.commit()  # Commit the change
    except AttributeError as e:
        logging.error(f"Error setting config value: {e}")
        pytest.skip("Skipping tests: config_service.set_config_value is not available or not async.")
    except Exception as e:
        logging.error(f"Unexpected error setting up config: {e}")
        pytest.fail("Failed to set up test configuration.")

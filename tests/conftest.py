import os

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
TestingSessionLocal = sessionmaker( autocommit=False, autoflush=False, bind=test_engine)

# Fixture to provide a test database session
@pytest_asyncio.fixture(scope="function") # Use pytest_asyncio.fixture for async
async def db_session():
    """Provides a clean transactional database session for tests."""
    # --- Schema Setup (Choose ONE method) ---
    # Method 1: Recreate schema every time (simple, ensures clean state)
    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all) # Make sure Base is imported
    #     await conn.run_sync(Base.metadata.create_all)

    # Method 2: Use Alembic (better if you have migrations)
    # alembic_cfg = Config("alembic.ini") # Assuming you have alembic.ini
    # command.upgrade(alembic_cfg, "head")

    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    # Rollback and close connection
    await session.close()
    await transaction.rollback()
    await connection.close()

    # --- Schema Teardown (if using Method 2) ---
    # command.downgrade(alembic_cfg, "base")


# Fixture to override the app's db session getter
@pytest.fixture(autouse=True)
def override_get_db_session(monkeypatch, db_session):
    """
    Monkeypatches the application's get_db_session to use the
    test database session for the duration of a test.
    NOTE: Adjust the import path 'app.database.get_db_session'
          to where your actual function is defined.
    """
    # Assuming your app uses a function like this:
    # async def get_db():
    #     async with SessionLocal() as session:
    #         yield session
    # You need to patch the dependency injection mechanism (e.g., FastAPI depends)
    # or the direct call if it's simpler like in the original code.

    # Patching the direct call in the service module (simpler given the original code)
    async def mock_get_db_session():
        # In the original code, get_db_session() returns a sync session.
        # If your app truly needs an *async* session EVERYWHERE, adjust.
        # This example assumes config_service can work with the async session
        # or you adapt config_service for async or provide a sync wrapper if needed.
        # Let's refine this based on config_service's needs.
        # IF config_service ONLY uses sync:
        # You might need a separate sync test engine/session for config_service tests
        # OR make config_service async compatible.
        # Assuming config_service is adapted or works with async session's sync methods:
        return db_session # Return the managed async session

    # Adjust the target path ('app.knowledge_sources.notion.services.get_db_session')
    # and ('app.services.config_service.get_db_session')
    # to where get_db_session is actually *imported* and *used*.
    try:
        # Patch where construct_headers imports it
        monkeypatch.setattr("app.knowledge_sources.notion.services.get_db_session", mock_get_db_session)
    except AttributeError:
         print("Warning: Could not patch get_db_session in notion services.")
         # This might happen if get_db_session isn't directly imported there.
         # You might need to patch app.database.get_db_session globally IF
         # that's feasible and doesn't break other parts of your test setup.

    try:
         # Patch where config_service might import it (or where it's called from)
        monkeypatch.setattr("app.services.config_service.get_db_session", mock_get_db_session)
    except AttributeError:
        print("Warning: Could not patch get_db_session in config_service.")

    # IMPORTANT: Ensure config_service can handle the async session
    # or provide a synchronous wrapper if needed for its operations.
    # If config_service strictly requires a sync session, you'll need a separate
    # sync testing setup or refactor config_service for async.


# Fixture to load Notion API key and other test IDs
@pytest.fixture(scope="session")
def notion_test_config():
    api_key = os.getenv("NOTION_API_KEY")
    page_id = os.getenv("TEST_NOTION_PAGE_ID")

    if not all([api_key, page_id]):
        pytest.skip("Skipping Notion integration tests: Required environment variables (.env.integration.test) not set.")

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
    # Assuming config_service has an async-compatible way to set config
    # OR adapt this call if config_service is purely synchronous
    from app.services import config_service  # Import locally to use patched DB

    # *** IMPORTANT REFACTORING NEEDED HERE ***
    # config_service.get_config_value was likely synchronous.
    # You need either:
    # 1. An async version: config_service.set_config_value_async(db_session, "notion_api_key", notion_test_config["api_key"])
    # 2. Run the sync version in a thread:
    #    await db_session.run_sync(config_service.set_config_value, "notion_api_key", notion_test_config["api_key"])
    # Let's assume you create an async version or adapt config_service
    # For demonstration, assuming an async set_config_value exists:
    await config_service.set_config_value(db_session, "notion_api_key", notion_test_config["api_key"])
    await db_session.commit() # Commit the change

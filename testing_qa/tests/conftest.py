"""
Pytest configuration and fixtures
"""
import os
import pytest
from framework.config import get_config, EnvironmentConfig
from framework.api.client import APIClient
from framework.lambda.invoker import LambdaInvoker
from framework.simulation.mock_server import MockServer
from framework.utils.test_data import TestDataManager
from framework.utils.logger import setup_logging


def pytest_configure(config):
    """Configure pytest"""
    # Setup logging
    log_level = config.getoption("--log-level", default="INFO")
    setup_logging(level=log_level)
    
    # Set environment from command line or default
    env_name = config.getoption("--env", default=None) or os.getenv("TEST_ENV", "dev")
    os.environ["TEST_ENV"] = env_name


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Environment to test (dev, qa, prod)"
    )
    parser.addoption(
        "--log-level",
        action="store",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )


@pytest.fixture(scope="session")
def config():
    """Get environment configuration"""
    env_name = pytest.config.getoption("--env") or os.getenv("TEST_ENV", "dev")
    return get_config(env_name)


@pytest.fixture(scope="session")
def api_client(config):
    """Get API client"""
    return APIClient()


@pytest.fixture(scope="session")
def lambda_invoker(config):
    """Get Lambda invoker"""
    return LambdaInvoker()


@pytest.fixture(scope="session")
def mock_server(config):
    """Get mock server manager"""
    server = MockServer()
    yield server
    server.stop_all_simulations()


@pytest.fixture(scope="function")
def test_data():
    """Get test data manager"""
    return TestDataManager()


@pytest.fixture(autouse=True)
def setup_simulations(mock_server, config):
    """Setup simulations before tests if needed"""
    # Start simulations for services configured to use them
    for service_name, service_config in config.downstream_services.items():
        if service_config.get("use_simulation", False):
            mock_server.start_service_simulation(service_name)
    yield
    # Cleanup handled by mock_server fixture


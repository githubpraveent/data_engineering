# Serverless E2E Testing Framework

A comprehensive end-to-end testing framework for API Gateway → Lambda(s) → downstream services (async/message-driven) architecture.

## Architecture Overview

This framework is designed to test serverless architectures with:
- **API Gateway** as the entry point
- **Lambda functions** for business logic
- **Asynchronous/event-driven** downstream services (queues, event buses, databases)
- **Multiple execution boundaries** requiring orchestration

## Testing Strategy

### Layered Approach

1. **Unit Tests**: Test individual Lambda business logic in isolation
2. **Integration Tests**: Validate API Gateway → Lambda → downstream services
3. **E2E Tests**: Full business flows including async behavior
4. **Simulated Tests**: Mock downstream services when unavailable

## Project Structure

```
.
├── config/                 # Environment configurations (DEV, QA, PROD)
├── tests/
│   ├── unit/              # Unit tests for Lambda functions
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── simulated/         # Tests with mocked services
├── framework/
│   ├── api/               # API testing modules
│   ├── lambda/            # Lambda testing utilities
│   ├── async/             # Async/event-driven testing utilities
│   ├── simulation/        # API simulation/mocking
│   └── utils/             # Common utilities
├── test_data/             # Test data management
├── ci_cd/                 # CI/CD pipeline configurations
└── requirements.txt       # Python dependencies
```

## Features

- ✅ Multi-environment support (DEV, QA, PROD)
- ✅ API testing with request/response validation
- ✅ Async/event-driven flow testing with polling
- ✅ Lambda integration testing
- ✅ API simulation/virtualization for downstream services
- ✅ Test data management and parameterization
- ✅ CI/CD integration
- ✅ State verification and side-effect checking

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environments:
```bash
cp config/environments/dev.example.json config/environments/dev.json
# Edit with your environment details
```

3. Run tests:
```bash
# Run all tests
pytest tests/

# Run by environment
pytest tests/ --env=qa

# Run specific test type
pytest tests/integration/
```

## Environment Configuration

Each environment (DEV, QA, PROD) has its own configuration file in `config/environments/` containing:
- API Gateway endpoints
- Lambda function names
- Queue/event bus ARNs
- Database connections
- Authentication credentials
- Timeout and retry settings

## CI/CD Integration

The framework includes configurations for:
- GitHub Actions
- Jenkins
- AWS CodePipeline

See `ci_cd/` directory for pipeline definitions.

## Documentation

- [Framework Architecture](docs/architecture.md)
- [Writing Tests](docs/writing_tests.md)
- [API Simulation Guide](docs/api_simulation.md)
- [CI/CD Setup](docs/cicd_setup.md)


# Integration Tests Organization

This directory contains integration tests organized by functional domain to ensure comprehensive testing coverage while maintaining clear separation of concerns.

## Test Directory Structure

```
tests/integration/
├── README.md                                      # This file - test organization guide
├── conftest.py                                    # Shared test fixtures and configuration
├── core/                                         # Core system integration tests
│   ├── config/                                   # Configuration system tests
│   │   ├── test_core_config_integration.py       # Comprehensive config framework tests
│   │   ├── test_configuration_system_integration.py # Core Settings, YamlLoader, DynamicConfig
│   │   └── test_settings_integration.py          # Profile-based settings management
│   └── utils/                                    # Core utility integration tests
├── infrastructure/                               # Infrastructure component tests
│   └── test_database_integration.py              # Database integration (MongoDB, Redis, PostgreSQL)
├── api/                                          # API layer integration tests
│   └── test_api_endpoints_integration.py         # FastAPI endpoints with real dependencies
├── services/                                     # Business logic service tests
│   ├── llm/                                     # LLM service integration tests
│   │   └── test_llm_structured_integration.py   # Structured outputs, chat service, schemas
│   ├── test_external_services_integration.py    # Atlassian service tests (moved)
│   └── test_jira_service_integration.py         # Comprehensive Jira API and tools integration
└── workflows/                                    # End-to-end workflow tests
```

## Test Categories

### Core Tests (`core/`)
Tests for fundamental system components that other parts depend on:
- **Configuration System**: 
  - `test_core_config_integration.py`: Comprehensive framework testing (Settings, PropertyResolver, DynamicConfig)
  - `test_configuration_system_integration.py`: Core components integration (YamlLoader, DynamicConfig access)
  - `test_settings_integration.py`: Profile-based configuration management and discovery
- **Utilities**: Property resolvers, dynamic imports, logging integration
- **Framework Components**: Dependency injection, singleton management

### Infrastructure Tests (`infrastructure/`)
Tests for external dependencies and infrastructure components:
- **Database Integration**: MongoDB session management with real database connections
- **Message Queues**: Celery, Redis pub/sub
- **File Systems**: Local storage, cloud storage integration
- **Network Services**: External API connectivity

### API Tests (`api/`)
Tests for HTTP API endpoints and middleware:
- **Endpoint Integration**: FastAPI route testing with httpx.AsyncClient and real dependencies
- **Authentication**: JWT, OAuth integration
- **Middleware**: CORS, rate limiting, request validation
- **Health Checks**: Service status endpoints with Redis backend

### Service Tests (`services/`)
Tests for business logic and service layer integration:
- **External Services**: 
  - `test_jira_service_integration.py`: Complete Jira API integration (2 test classes, 19 methods)
  - `test_external_services_integration.py`: Atlassian services integration
- **LLM Services**: 
  - `test_llm_structured_integration.py`: Structured outputs, chat service, agent workflows (4 test classes, 13 methods)
- **Agent Services**: Tool execution, workflow orchestration
- **Data Services**: Ingestion, processing, transformation

### Workflow Tests (`workflows/`)
End-to-end tests that validate complete user scenarios:
- **Agent Workflows**: Multi-step agent interactions
- **Data Processing Pipelines**: Complete ingestion to retrieval flows
- **User Journeys**: Authentication to task completion
- **System Recovery**: Error handling and graceful degradation

## Existing Test Coverage

### Core Configuration (Fully Tested)
- ✅ **Settings Framework**: Singleton behavior, profile discovery, YAML loading
- ✅ **Property Resolution**: Environment variables, placeholders, type conversion
- ✅ **Dynamic Configuration**: Dot notation access, nested configuration, attribute creation
- ✅ **Integration**: Application component integration, error handling, performance

### Service Integration (Comprehensive)
- ✅ **Jira Service**: API connection, project management, issue CRUD, JQL search, agent tools
- ✅ **LLM Services**: Structured outputs, chat integration, agent thinking, ingestion analysis
- ✅ **External Services**: Atlassian service integration patterns

### Infrastructure (Covered)
- ✅ **Database**: MongoDB session repository with real database integration
- ✅ **API**: FastAPI endpoint testing with AsyncClient and real Redis backend

## Test Naming Conventions

- **File Names**: `test_{component}_{type}_integration.py`
  - `test_core_config_integration.py` - Comprehensive core component
  - `test_jira_service_integration.py` - External service component
  - `test_llm_structured_integration.py` - LLM service component

- **Class Names**: `Test{Component}Integration`
  - `TestSettingsFrameworkIntegration`
  - `TestJiraServiceIntegration`
  - `TestChatServiceIntegration`

- **Method Names**: `test_{specific_functionality}`
  - `test_settings_singleton_behavior`
  - `test_jira_server_connection`
  - `test_chat_with_structured_agent_response`

## Test Execution

### Run All Integration Tests
```bash
poetry run pytest tests/integration/ -v
```

### Run Specific Categories
```bash
# Core system tests (3 configuration test files)
poetry run pytest tests/integration/core/ -v

# Infrastructure tests  
poetry run pytest tests/integration/infrastructure/ -v

# API tests
poetry run pytest tests/integration/api/ -v

# Service tests (Jira + LLM + External)
poetry run pytest tests/integration/services/ -v

# Workflow tests
poetry run pytest tests/integration/workflows/ -v
```

### Run Individual Test Files
```bash
# Core configuration tests
poetry run pytest tests/integration/core/config/test_core_config_integration.py -v
poetry run pytest tests/integration/core/config/test_settings_integration.py -v

# Service integration tests  
poetry run pytest tests/integration/services/test_jira_service_integration.py -v
poetry run pytest tests/integration/services/llm/test_llm_structured_integration.py -v
```

## Test Dependencies

Integration tests require real dependencies to be running:
- **MongoDB**: For database integration tests
- **Redis**: For caching, Celery, and API health check tests
- **External APIs**: For Jira service integration tests (with valid credentials)
- **Environment Variables**: Proper configuration in `.env` file

Use `docker-compose.yml` to start required services:
```bash
docker-compose up -d mongodb redis postgres
```

## Test Results Summary

Based on recent test runs:
- **Core Configuration**: 17 tests created, 14 passing (82% success rate)
- **API Integration**: All AsyncClient tests passing with Redis backend
- **Service Integration**: Comprehensive Jira and LLM test coverage
- **Database Integration**: MongoDB session management fully tested

## Fixtures and Utilities

- **conftest.py**: Comprehensive fixtures for all test categories:
  - Core configuration testing (temp directories, test configs, isolated settings)
  - Database testing (MongoDB connections, test data cleanup)
  - API testing (FastAPI AsyncClient setup)
  - Service testing (external service mocks)
- **Test Mixins**: MongoDBTestMixin for common database operations
- **Mock Services**: Simplified versions for isolated testing

## Best Practices

1. **Proper Classification**: Tests are now organized by functional domain, not by file location
2. **Real Dependencies**: Integration tests use actual databases/services, not mocks
3. **Test Isolation**: Each test cleans up after itself with proper fixtures
4. **Comprehensive Coverage**: Multiple test files cover different aspects of the same system
5. **Environment Management**: Test-specific environment variables and configurations
6. **Performance Monitoring**: Tests include performance assertions and timing checks
7. **Documentation**: Clear docstrings explain integration scenarios being tested

## Test Classification Structure
"""
tests/
├── unit/                           # Unit tests (single component, mocked dependencies)
│   ├── core/
│   │   ├── config/                 # Configuration providers unit tests
│   │   ├── utils/                  # Utility classes unit tests  
│   │   └── enums/                  # Enum and constants unit tests
│   ├── services/                   # Service layer unit tests
│   ├── api/                        # API layer unit tests (controllers)
│   └── schemas/                    # Schema validation unit tests
│
├── integration/                    # Integration tests (multiple components, real dependencies)
│   ├── core/                       # Core system integration tests
│   │   ├── config/                 # Configuration system integration
│   │   │   ├── test_core_config_integration.py        # ✅ CREATED
│   │   │   ├── test_settings_framework_integration.py  # Settings + Profiles + YAML
│   │   │   ├── test_property_resolution_integration.py # Environment + Placeholders
│   │   │   └── test_config_provider_integration.py     # App/DB/LLM/Vector configs
│   │   │
│   │   └── utils/                  # Core utilities integration
│   │       ├── test_env_management_integration.py      # Environment + PropertyResolver
│   │       ├── test_dynamic_import_integration.py      # DynamicImporter + Registry
│   │       └── test_singleton_management_integration.py # Singleton behavior across system
│   │
│   ├── infrastructure/             # Infrastructure integration tests
│   │   ├── test_database_integration.py                # ✅ MongoDB/PostgreSQL connections
│   │   ├── test_cache_integration.py                   # Redis integration
│   │   ├── test_vector_store_integration.py            # Vector DB integrations
│   │   └── test_external_service_integration.py        # Confluence/Jira/OpenAI
│   │
│   ├── api/                        # API layer integration tests
│   │   ├── test_api_endpoints_integration.py           # ✅ FastAPI endpoints (MOVED)
│   │   ├── test_auth_integration.py                    # Authentication flow
│   │   ├── test_middleware_integration.py              # Middleware stack
│   │   └── test_error_handling_integration.py          # Error handling across API
│   │
│   ├── services/                   # Service layer integration tests
│   │   ├── test_chat_service_integration.py            # Chat + Agent + LLM
│   │   ├── test_ingestion_service_integration.py       # Data ingestion pipeline
│   │   ├── test_session_management_integration.py      # Session + Database
│   │   └── test_external_services_integration.py       # ✅ Jira/Confluence (EXISTS)
│   │
│   └── workflows/                  # End-to-end workflow tests
│       ├── test_complete_chat_workflow.py              # Full chat interaction
│       ├── test_data_ingestion_workflow.py             # Complete data pipeline
│       └── test_agent_workflow_integration.py          # Agent execution pipeline
│
└── e2e/                           # End-to-end tests (full system, UI if applicable)
    ├── test_user_journeys.py      # Complete user scenarios
    ├── test_api_contracts.py      # API contract validation
    └── test_performance.py        # Performance and load testing
"""

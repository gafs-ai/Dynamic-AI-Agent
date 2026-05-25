# ModelComponent Test Suite

These integration tests require a reachable SurrealDB instance.
All secret configuration files are prefixed with `secret_test_` to avoid
accidental commits.

## Prerequisites

1. Create `secret_test_db_config.json` in this directory with your database
   connection settings:
   ```json
   {
     "endpoint":  "wss://<host>/rpc",
     "namespace": "<namespace>",
     "database":  "<database>",
     "username":  "<username>",
     "password":  "<password>"
   }
   ```

2. For live Azure OpenAI integration tests (model service invoke tests),
   create `secret_test_secret_azure_openai_japan_east.json`:
   ```json
   {
     "name": "<secret-name>",
     "raw_secret": { "api_key": "<azure-openai-api-key>" },
     "description": "Azure OpenAI API key"
   }
   ```

## Running Tests

All tests (skips DB tests if config is missing):
```
pytest Python/gafs/dynamicaiagent/modelcomponent/test/ -v
```

Only ModelCatalogueService tests:
```
pytest Python/gafs/dynamicaiagent/modelcomponent/test/test_model_catalogue_service.py -v
```

Only ModelService tests (live invoke tests skipped if fixtures absent):
```
pytest Python/gafs/dynamicaiagent/modelcomponent/test/test_model_service.py -v
```

Only ModelComponent tests:
```
pytest Python/gafs/dynamicaiagent/modelcomponent/test/test_model_component.py -v
```

## Test Files

| File | Description |
|------|-------------|
| `conftest.py` | Shared fixtures (DB manager, component wiring, stub AI) |
| `test_model_catalogue_service.py` | Integration tests for `ModelCatalogueService` |
| `test_model_service.py` | Integration tests for `ModelService` (stub + live) |
| `test_model_component.py` | Integration tests for `ModelComponent` facade |
| `test_build_modelcomponent.py` | Tests for the Nuitka compiled build output |

## Secret Fixture Files

| File | Contents |
|------|----------|
| `secret_test_db_config.json` | SurrealDB connection settings |
| `secret_test_secret_azure_openai_japan_east.json` | Azure OpenAI API key |
| `secret_test_deployment_azure_embedding.json` | Embedding deployment config |
| `secret_test_deployment_azure_chat.json` | Chat completion deployment config |
| `secret_test_catalogue_azure_embedding.json` | Embedding model catalogue entry |
| `secret_test_catalogue_azure_chat.json` | Chat completion model catalogue entry |
| `secret_test_invoke_chat_0.json` | Chat completion request for live tests |
| `secret_test_invoke_embedding_0.json` | Embedding request for live tests |

## Test Results

Last verified run: **22 passed** (2026-05-25).

```
======================= 22 passed in 135.74s (0:02:15) ========================
```


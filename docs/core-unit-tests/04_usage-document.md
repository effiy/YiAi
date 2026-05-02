# core-unit-tests — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6

## Usage Overview

This document guides developers in running and extending the YiAi test suite.

## Running Tests

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run all tests

```bash
pytest tests/ -v
```

### Run a specific test file

```bash
pytest tests/test_execution.py -v
pytest tests/test_upload.py -v
```

### Run with coverage (if pytest-cov installed)

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Writing New Tests

### Test file naming

Name test files `test_<module>.py` and place them in `tests/`.

### Test function naming

Prefix test functions with `test_`:

```python
def test_my_feature():
    assert my_feature() == expected
```

### Using fixtures

Import shared fixtures from `conftest.py`:

```python
def test_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

### Async tests

Use `pytest-asyncio` for async functions:

```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    result = await async_feature()
    assert result == expected
```

### Mocking settings

Use `monkeypatch` for configuration isolation:

```python
def test_with_custom_dir(temp_static_dir):
    # temp_static_dir is a tmp_path monkeypatched to settings.static_base_dir
    pass
```

## Postscript: Future Planning & Improvements

- Document mocking patterns for MongoDB and OSS when integration tests are added.

# Test Organization

This directory contains all tests for KanardiaCloud organized into logical categories:

## Directory Structure

- **`api/`** - API endpoint tests
- **`integration/`** - Integration tests for complex workflows
- **`models/`** - Database model tests
- **`security/`** - Security and CSRF protection tests  
- **`unit/`** - Unit tests for individual components

## Running Tests

To run all tests:
```bash
python -m pytest tests/ -v
```

To run specific test categories:
```bash
# Run only API tests
python -m pytest tests/api/ -v

# Run only unit tests
python -m pytest tests/unit/ -v

# Run only integration tests
python -m pytest tests/integration/ -v

# Run only model tests
python -m pytest tests/models/ -v

# Run only security tests
python -m pytest tests/security/ -v
```

## Test Naming Convention

All test files follow the pattern `test_*.py` to be automatically discovered by pytest.

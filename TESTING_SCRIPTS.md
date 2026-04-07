# Test Scripts

This directory contains PowerShell scripts for running tests and code quality checks.

## run_all_tests.ps1

The main test runner script that executes the test suite and optional code quality tools.

### Basic Usage

Run all tests:
```powershell
.\run_all_tests.ps1
```

### Advanced Usage

#### Run tests with all code quality tools
```powershell
.\run_all_tests.ps1 -All
```

This enables all code quality tools:
- **Radon**: Complexity analysis for Python code
- **Ruff**: Fast Python linter
- **Mypy**: Static type checker
- **Bandit**: Security vulnerability scanner
- **Coverage**: Test coverage analysis

#### Run tests with specific filter
```powershell
# Run only tests matching "spell"
.\run_all_tests.ps1 -Filter "spell"

# Run only tests matching "equipment"
.\run_all_tests.ps1 -Filter "equipment"
```

#### Run tests with individual tools
```powershell
# Run tests with Ruff linter only
.\run_all_tests.ps1 -Ruff

# Run tests with type checking only
.\run_all_tests.ps1 -Mypy

# Run tests with security scan only
.\run_all_tests.ps1 -Bandit

# Run tests with coverage report only
.\run_all_tests.ps1 -Coverage

# Run tests with complexity analysis only
.\run_all_tests.ps1 -Radon
```

#### Combine multiple tools
```powershell
# Run tests with linting and type checking
.\run_all_tests.ps1 -Ruff -Mypy

# Run tests with security scan and coverage
.\run_all_tests.ps1 -Bandit -Coverage

# Run tests with all tools except Radon
.\run_all_tests.ps1 -Ruff -Mypy -Bandit -Coverage
```

#### Combine filter with tools
```powershell
# Run spell tests with all tools
.\run_all_tests.ps1 -Filter "spell" -All

# Run equipment tests with linting
.\run_all_tests.ps1 -Filter "equipment" -Ruff
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `-Filter` | String | Filter tests by keyword (passed to pytest `-k` option) |
| `-All` | Switch | Enable all code quality tools (Radon, Ruff, Mypy, Bandit, Coverage) |
| `-Radon` | Switch | Run Radon complexity analysis |
| `-Ruff` | Switch | Run Ruff linter |
| `-Mypy` | Switch | Run Mypy type checker |
| `-Bandit` | Switch | Run Bandit security scanner |
| `-Coverage` | Switch | Generate test coverage report |

### Output

The script provides clear, color-coded output:
- **Cyan**: Section headers
- **Green**: Success messages
- **Red**: Failure messages
- **Yellow**: Tool section headers

### Test Suites

The script runs two separate test suites:

1. **Main test suite**: All tests except equipment events tests
2. **Equipment events tests**: Run separately to avoid mock contamination

### Exit Codes

- `0`: All tests passed
- `1`: Some tests failed

## Examples

### Development Workflow
```powershell
# Quick test run during development
.\run_all_tests.ps1

# Full check before committing
.\run_all_tests.ps1 -All

# Check specific feature
.\run_all_tests.ps1 -Filter "armor_manager" -Ruff -Mypy
```

### CI/CD Pipeline
```powershell
# Comprehensive check for CI/CD
.\run_all_tests.ps1 -All
```

### Code Review
```powershell
# Focus on code quality for review
.\run_all_tests.ps1 -Ruff -Mypy -Bandit
```

## Other Test Scripts

### run_checks.ps1
Runs various code quality checks without running the full test suite.

### run_vulture.ps1
Runs Vulture to find unused code.

## See Also

- [TESTING.md](docs/TESTING.md) - Testing strategy and patterns
- [TEST_SUITE.md](docs/TEST_SUITE.md) - Detailed test suite documentation

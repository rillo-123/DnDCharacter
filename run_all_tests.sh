#!/bin/bash
# Run all tests for the DnD Character project
# Usage: ./run_all_tests.sh [options]
# Options:
#   -f, --filter FILTER    Filter tests by pattern
#   -a, --all              Run all code quality tools
#   --radon                Run radon complexity analysis
#   --ruff                 Run ruff linter
#   --mypy                 Run mypy type checker
#   --bandit               Run bandit security scanner
#   --coverage             Run test coverage report

set -e

# Parse command line arguments
FILTER=""
ALL=false
RADON=false
RUFF=false
MYPY=false
BANDIT=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--filter)
            FILTER="$2"
            shift 2
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        --radon)
            RADON=true
            shift
            ;;
        --ruff)
            RUFF=true
            shift
            ;;
        --mypy)
            MYPY=true
            shift
            ;;
        --bandit)
            BANDIT=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-f FILTER] [-a|--all] [--radon] [--ruff] [--mypy] [--bandit] [--coverage]"
            exit 1
            ;;
    esac
done

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build path to the venv python executable
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "Error: Python not found. Please install Python or create a virtual environment."
    exit 1
fi

# If --all is specified, enable all tools
if [ "$ALL" = true ]; then
    RADON=true
    RUFF=true
    MYPY=true
    BANDIT=true
    COVERAGE=true
fi

TOOLS_ENABLED=false
if [ "$RADON" = true ] || [ "$RUFF" = true ] || [ "$MYPY" = true ] || [ "$BANDIT" = true ] || [ "$COVERAGE" = true ]; then
    TOOLS_ENABLED=true
fi

# ANSI color codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}Running Main Test Suite${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Run main test suite (excluding equipment_events to avoid mock contamination)
MAIN_PYTEST_ARGS=("-m" "pytest" "tests" "--ignore=tests/test_equipment_chooser.py" "--ignore=tests/test_equipment_events.py")
if [ -n "$FILTER" ]; then
    MAIN_PYTEST_ARGS+=("-k" "$FILTER")
fi

if "$PYTHON" "${MAIN_PYTEST_ARGS[@]}"; then
    MAIN_EXIT_CODE=0
else
    MAIN_EXIT_CODE=$?
fi

echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}Running Equipment Events Tests${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Run equipment events tests separately (requires browser module mocking)
if "$PYTHON" -m pytest tests/test_equipment_events.py -v; then
    EVENTS_EXIT_CODE=0
else
    EVENTS_EXIT_CODE=$?
fi

echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}Test Suite Summary${NC}"
echo -e "${CYAN}========================================${NC}\n"

if [ $MAIN_EXIT_CODE -eq 0 ] && [ $EVENTS_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[OK] All tests passed!${NC}"
    echo -e "${GREEN}  - Main test suite: PASSED${NC}"
    echo -e "${GREEN}  - Equipment events tests: PASSED${NC}"
else
    echo -e "${RED}[FAIL] Some tests failed:${NC}"
    if [ $MAIN_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}  - Main test suite: FAILED (exit code $MAIN_EXIT_CODE)${NC}"
    else
        echo -e "${GREEN}  - Main test suite: PASSED${NC}"
    fi
    if [ $EVENTS_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}  - Equipment events tests: FAILED (exit code $EVENTS_EXIT_CODE)${NC}"
    else
        echo -e "${GREEN}  - Equipment events tests: PASSED${NC}"
    fi
fi

# Run code quality tools if requested
if [ "$TOOLS_ENABLED" = true ]; then
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}Code Quality Tools${NC}"
    echo -e "${CYAN}========================================${NC}\n"
    
    if [ "$RADON" = true ]; then
        echo -e "\n${YELLOW}--- Radon Complexity Analysis ---${NC}"
        "$PYTHON" -m radon cc static/assets/py -s -nb
        echo ""
    fi
    
    if [ "$RUFF" = true ]; then
        echo -e "\n${YELLOW}--- Ruff Linter ---${NC}"
        "$PYTHON" -m ruff check static/assets/py --statistics
        echo ""
    fi
    
    if [ "$MYPY" = true ]; then
        echo -e "\n${YELLOW}--- Mypy Type Checker ---${NC}"
        # Capture output but suppress only the error summary
        if "$PYTHON" -m mypy static/assets/py --ignore-missing-imports --no-error-summary; then
            echo -e "${GREEN}[OK] No type errors found${NC}"
        fi
        echo ""
    fi
    
    if [ "$BANDIT" = true ]; then
        echo -e "\n${YELLOW}--- Bandit Security Scanner ---${NC}"
        "$PYTHON" -m bandit -r static/assets/py -q -f screen
        echo ""
    fi
    
    if [ "$COVERAGE" = true ]; then
        echo -e "\n${YELLOW}--- Test Coverage Report ---${NC}"
        "$PYTHON" -m coverage run -m pytest tests --ignore=tests/test_equipment_chooser.py --ignore=tests/test_equipment_events.py -q
        "$PYTHON" -m coverage report --include="static/assets/py/*" --omit="*/__pycache__/*"
        echo ""
    fi
    
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}Code Quality Summary${NC}"
    echo -e "${CYAN}========================================${NC}\n"
    
    if [ "$RADON" = true ]; then echo -e "${GREEN}[OK] Complexity analysis complete${NC}"; fi
    if [ "$RUFF" = true ]; then echo -e "${GREEN}[OK] Linting complete${NC}"; fi
    if [ "$MYPY" = true ]; then echo -e "${GREEN}[OK] Type checking complete${NC}"; fi
    if [ "$BANDIT" = true ]; then echo -e "${GREEN}[OK] Security scan complete${NC}"; fi
    if [ "$COVERAGE" = true ]; then echo -e "${GREEN}[OK] Coverage report complete${NC}"; fi
fi

# Exit with appropriate code
if [ $MAIN_EXIT_CODE -eq 0 ] && [ $EVENTS_EXIT_CODE -eq 0 ]; then
    exit 0
else
    exit 1
fi

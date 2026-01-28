# Frontend Testing Guide

## Overview

The frontend test suite uses Playwright for end-to-end testing, covering all major UI functionality, user interactions, and visual elements.

## Test Structure

### Test Suites

1. **Theme Toggle Tests** (`test_theme_toggle.py`)
   - Theme switching (light/dark mode)
   - Theme persistence (localStorage)
   - Keyboard navigation
   - Accessibility features
   - Visual appearance
   - Footer visibility

2. **Chat Functionality Tests** (`test_chat_functionality.py`)
   - Initial page load and welcome message
   - Send message and receive response
   - New chat button functionality
   - Course statistics loading
   - Suggested questions
   - Error handling
   - Keyboard shortcuts (Enter key)

3. **UI Components Tests** (`test_ui_components.py`)
   - Sidebar collapsibles
   - Layout structure
   - Responsive design (desktop, tablet, mobile)
   - Message display formatting
   - Scroll behavior
   - Accessibility features

## Running Tests

### Run All Frontend Tests
```powershell
python frontend/tests/run_all_tests.py
```

### Run Individual Test Suites
```powershell
# Theme toggle tests
python frontend/tests/test_theme_toggle.py

# Chat functionality tests
python frontend/tests/test_chat_functionality.py

# UI components tests
python frontend/tests/test_ui_components.py
```

## Pre-Push Hook

The pre-push git hook automatically runs all tests before pushing to prevent broken code:

**Tests run on push:**
1. Backend pytest tests (86 tests)
2. Frontend theme toggle tests
3. Frontend chat functionality tests
4. Frontend UI components tests

**Audio Feedback:**
- ✅ Success: "Great, all tests passed successfully"
- ❌ Failure: "Oh no, some tests failed"

## Test Coverage

### Frontend Coverage
- ✅ Theme switching and persistence
- ✅ Chat message sending/receiving
- ✅ Session management
- ✅ New chat functionality
- ✅ Course statistics display
- ✅ Suggested questions
- ✅ Error handling
- ✅ Responsive design
- ✅ Accessibility features
- ✅ Keyboard navigation
- ✅ Message display and sources
- ✅ Scroll behavior
- ✅ Collapsible sections

### Backend Coverage
- ✅ API endpoints (/api/query, /api/courses, /api/clear-session)
- ✅ RAG system integration
- ✅ AI generator
- ✅ Search tools
- ✅ Edge cases and error handling

## Test Requirements

### Prerequisites
```powershell
# Install test dependencies
pip install pytest pytest-cov playwright

# Install Playwright browsers
playwright install chromium
```

### Server Requirements
Tests require the application server to be running:
```powershell
# Start the server (in a separate terminal)
python main.py
# or
./run.ps1
```

The tests expect the application at `http://localhost:8000`

## Writing New Tests

### Test Structure
```python
async def test_feature_name():
    """Test description"""
    print("\n=== Testing Feature ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Test steps
            await page.goto("http://localhost:8000")
            # ... test logic ...
            
            print("\n=== Test Passed! ===\n")
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            await browser.close()
            return False
```

### Best Practices
1. Use descriptive test names and docstrings
2. Print progress messages for debugging
3. Wait for elements with appropriate timeouts
4. Clean up browser instances in finally blocks
5. Return True/False for pass/fail status
6. Keep tests independent (no shared state)
7. Use `headless=False` during development for visibility

## CI/CD Integration

The tests are integrated into the git workflow:

1. **Pre-commit**: Code formatting checks (optional)
2. **Pre-push**: Full test suite execution (required)
   - Backend tests must pass
   - All frontend E2E tests must pass
   - Push is blocked if any test fails

## Troubleshooting

### Tests Fail to Start
- Ensure server is running at `http://localhost:8000`
- Check virtual environment is activated
- Verify Playwright browsers are installed

### Timeout Errors
- Increase timeout values in tests
- Check network connection
- Ensure server is responding

### Visual Test Failures
- Check screenshots in `frontend/tests/`
- Verify CSS changes haven't broken layout
- Test in different browsers if needed

## Test Maintenance

### Adding New Features
When adding new frontend features:
1. Write E2E tests covering the feature
2. Add tests to appropriate test file
3. Update this documentation
4. Verify pre-push hook runs new tests

### Updating Existing Tests
When modifying UI:
1. Update affected tests
2. Run full test suite
3. Fix any failures before committing
4. Update documentation if test behavior changes

## Performance

- **Backend tests**: ~10 seconds (86 tests)
- **Theme toggle tests**: ~30 seconds (12 tests)
- **Chat functionality tests**: ~60 seconds (7 tests)
- **UI components tests**: ~45 seconds (6 tests)
- **Total test time**: ~2-3 minutes

## Test Reports

Test results include:
- Individual test status (✓ PASSED / ✗ FAILED)
- Suite summaries
- Final overall summary
- Screenshots for visual tests (theme-light.png, theme-dark.png)

## Future Enhancements

Potential test additions:
- Performance/load testing
- Cross-browser testing (Firefox, Safari)
- Mobile device testing
- API integration tests with mocked backend
- Accessibility compliance testing (WCAG)
- Visual regression testing

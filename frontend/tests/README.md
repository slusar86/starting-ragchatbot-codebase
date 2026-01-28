# Frontend E2E Tests

This directory contains End-to-End (E2E) tests for the frontend using Playwright.

## Tests

### `test_theme_toggle.py`
E2E tests for the theme toggle button functionality.

**Test Coverage:**
- ✅ Button visibility and existence
- ✅ Initial theme state
- ✅ Accessibility attributes (ARIA labels, title)
- ✅ Mouse click toggling
- ✅ Keyboard navigation (Space and Enter keys)
- ✅ LocalStorage persistence
- ✅ Theme persistence after page reload
- ✅ CSS transitions and animations
- ✅ Icon visibility and opacity
- ✅ Hover effects
- ✅ Visual appearance (screenshots)

## Prerequisites

```bash
# Install Playwright
pip install playwright

# Install browser drivers
python -m playwright install
```

## Running Tests

### Run all theme toggle tests:
```bash
cd frontend/tests
python test_theme_toggle.py
```

### Requirements:
- Application must be running on `http://localhost:8000`
- Start the backend server before running tests

## Test Output

Tests will:
- Display detailed progress in console
- Create screenshots in `frontend/tests/`:
  - `theme-light.png` - Light theme screenshot
  - `theme-dark.png` - Dark theme screenshot
- Show browser window during execution (headless=False)

## Test Structure

Each test suite includes:
1. **Setup**: Launch browser and navigate to app
2. **Assertions**: Verify functionality
3. **Cleanup**: Close browser
4. **Summary**: Show pass/fail status

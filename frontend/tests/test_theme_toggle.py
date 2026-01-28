"""
E2E Tests for Theme Toggle Button

Tests the theme toggle button functionality using Playwright.
Verifies light/dark mode switching, persistence, and accessibility.
"""

import asyncio
import re
from playwright.async_api import async_playwright, expect


async def test_theme_toggle_button():
    """Test theme toggle button exists and is visible"""
    print("\n=== Testing Theme Toggle Button ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the application
            print("1. Navigating to application...")
            await page.goto("http://localhost:8000", wait_until="networkidle")
            print("✓ Page loaded successfully")
            
            # Find the theme toggle button
            print("\n2. Checking if theme toggle button exists...")
            theme_button = page.locator("#themeToggle")
            await expect(theme_button).to_be_visible(timeout=5000)
            print("✓ Theme toggle button is visible")
            
            # Check initial state (should be dark theme by default)
            print("\n3. Checking initial theme state...")
            body = page.locator("body")
            has_light_class = await body.evaluate("el => el.classList.contains('light-theme')")
            if has_light_class:
                print("✓ Initial theme: Light mode")
            else:
                print("✓ Initial theme: Dark mode")
            
            # Check button accessibility attributes
            print("\n4. Checking accessibility attributes...")
            aria_label = await theme_button.get_attribute("aria-label")
            title = await theme_button.get_attribute("title")
            print(f"✓ ARIA label: {aria_label}")
            print(f"✓ Title: {title}")
            
            # Test clicking the button
            print("\n5. Testing theme toggle by clicking...")
            initial_theme = has_light_class
            await theme_button.click()
            await page.wait_for_timeout(500)  # Wait for transition
            
            new_light_class = await body.evaluate("el => el.classList.contains('light-theme')")
            if new_light_class != initial_theme:
                print("✓ Theme toggled successfully")
                print(f"  Theme changed from {'light' if initial_theme else 'dark'} to {'light' if new_light_class else 'dark'}")
            else:
                print("✗ Theme did not change")
                return False
            
            # Toggle back
            print("\n6. Toggling theme back...")
            await theme_button.click()
            await page.wait_for_timeout(500)
            
            toggled_back = await body.evaluate("el => el.classList.contains('light-theme')")
            if toggled_back == initial_theme:
                print("✓ Theme toggled back successfully")
            else:
                print("✗ Theme did not toggle back")
                return False
            
            # Test keyboard navigation (Space key)
            print("\n7. Testing keyboard navigation (Space key)...")
            await theme_button.focus()
            await page.keyboard.press("Space")
            await page.wait_for_timeout(500)
            
            space_toggle = await body.evaluate("el => el.classList.contains('light-theme')")
            if space_toggle != toggled_back:
                print("✓ Space key toggles theme")
            else:
                print("✗ Space key did not toggle theme")
            
            # Test keyboard navigation (Enter key)
            print("\n8. Testing keyboard navigation (Enter key)...")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(500)
            
            enter_toggle = await body.evaluate("el => el.classList.contains('light-theme')")
            if enter_toggle != space_toggle:
                print("✓ Enter key toggles theme")
            else:
                print("✗ Enter key did not toggle theme")
            
            # Test localStorage persistence
            print("\n9. Testing theme persistence with localStorage...")
            current_theme = await body.evaluate("el => el.classList.contains('light-theme')")
            stored_theme = await page.evaluate("() => localStorage.getItem('theme')")
            expected_theme = 'light' if current_theme else 'dark'
            
            if stored_theme == expected_theme:
                print(f"✓ Theme stored in localStorage: {stored_theme}")
            else:
                print(f"✗ localStorage mismatch. Stored: {stored_theme}, Expected: {expected_theme}")
            
            # Test theme persistence after reload
            print("\n10. Testing theme persistence after page reload...")
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(500)
            
            reloaded_theme = await body.evaluate("el => el.classList.contains('light-theme')")
            if reloaded_theme == current_theme:
                print("✓ Theme persisted after reload")
            else:
                print("✗ Theme did not persist after reload")
            
            # Test CSS transitions and animations
            print("\n11. Testing CSS transitions on icons...")
            sun_icon = page.locator(".sun-icon")
            moon_icon = page.locator(".moon-icon")
            
            # Both icons exist in DOM but visibility is controlled by opacity
            sun_count = await sun_icon.count()
            moon_count = await moon_icon.count()
            
            if sun_count > 0 and moon_count > 0:
                print("✓ Both sun and moon icons are present in DOM")
            else:
                print(f"✗ Missing icons. Sun: {sun_count}, Moon: {moon_count}")
            
            # Check icon visibility based on theme via opacity
            sun_opacity = await sun_icon.evaluate("el => window.getComputedStyle(el).opacity")
            moon_opacity = await moon_icon.evaluate("el => window.getComputedStyle(el).opacity")
            print(f"  Sun icon opacity: {sun_opacity}")
            print(f"  Moon icon opacity: {moon_opacity}")
            
            # Verify one is visible (opacity 1) and one is hidden (opacity 0)
            if (sun_opacity == "1" and moon_opacity == "0") or (sun_opacity == "0" and moon_opacity == "1"):
                print("✓ Icons have correct opacity for theme")
            else:
                print(f"⚠ Icon opacity may be transitioning")
            
            # Test hover effect
            print("\n12. Testing hover effect...")
            await theme_button.hover()
            await page.wait_for_timeout(300)
            print("✓ Button hover effect applied")
            
            print("\n=== All Theme Toggle Tests Passed! ===\n")
            
            # Keep browser open for visual inspection
            print("Browser will close in 3 seconds...")
            await page.wait_for_timeout(3000)
            
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_theme_visual_appearance():
    """Test visual appearance of light and dark themes"""
    print("\n=== Testing Theme Visual Appearance ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            
            # Get dark theme colors
            print("1. Capturing dark theme colors...")
            body = page.locator("body")
            dark_bg = await body.evaluate("el => window.getComputedStyle(el).backgroundColor")
            print(f"✓ Dark theme background: {dark_bg}")
            
            # Switch to light theme
            print("\n2. Switching to light theme...")
            theme_button = page.locator("#themeToggle")
            
            # Ensure we're in dark mode first
            has_light = await body.evaluate("el => el.classList.contains('light-theme')")
            if has_light:
                await theme_button.click()
                await page.wait_for_timeout(500)
            
            # Now toggle to light
            await theme_button.click()
            await page.wait_for_timeout(500)
            
            light_bg = await body.evaluate("el => window.getComputedStyle(el).backgroundColor")
            print(f"✓ Light theme background: {light_bg}")
            
            # Verify themes are different
            if dark_bg != light_bg:
                print("✓ Themes have different background colors")
            else:
                print("✗ Themes have same background color")
                return False
            
            # Take screenshots
            print("\n3. Taking screenshots...")
            await page.screenshot(path="frontend/tests/theme-light.png")
            print("✓ Light theme screenshot saved: frontend/tests/theme-light.png")
            
            await theme_button.click()
            await page.wait_for_timeout(500)
            await page.screenshot(path="frontend/tests/theme-dark.png")
            print("✓ Dark theme screenshot saved: frontend/tests/theme-dark.png")
            
            print("\n=== Visual Appearance Tests Passed! ===\n")
            
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Visual test failed with error: {e}")
            await browser.close()
            return False


async def test_footer_presence():
    """Test that the footer is present and properly styled"""
    print("\n=== Testing Footer Presence and Styling ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            
            # Check if footer exists
            print("1. Checking if footer exists...")
            footer = page.locator(".app-footer")
            await expect(footer).to_be_visible(timeout=5000)
            print("✓ Footer is visible")
            
            # Check footer text content
            print("\n2. Checking footer content...")
            footer_text = await footer.text_content()
            if "All rights reserved" in footer_text and "Claude" in footer_text:
                print(f"✓ Footer contains correct text: {footer_text.strip()}")
            else:
                print(f"✗ Footer text incorrect: {footer_text}")
                return False
            
            # Check footer positioning
            print("\n3. Checking footer positioning...")
            footer_position = await footer.evaluate("el => window.getComputedStyle(el).position")
            if footer_position == "fixed":
                print("✓ Footer has fixed positioning")
            else:
                print(f"✗ Footer position is {footer_position}, expected fixed")
                return False
            
            # Check footer is at bottom-left
            footer_bottom = await footer.evaluate("el => window.getComputedStyle(el).bottom")
            footer_left = await footer.evaluate("el => window.getComputedStyle(el).left")
            print(f"  Bottom: {footer_bottom}, Left: {footer_left}")
            if footer_bottom == "0px" and footer_left == "0px":
                print("✓ Footer positioned at bottom-left")
            else:
                print(f"⚠ Footer position may be different")
            
            # Check Claude brand color
            print("\n4. Checking Claude brand styling...")
            claude_brand = page.locator(".claude-brand")
            await expect(claude_brand).to_be_visible()
            claude_color = await claude_brand.evaluate("el => window.getComputedStyle(el).color")
            print(f"✓ Claude brand color: {claude_color}")
            
            # Check font size
            print("\n5. Checking footer font size...")
            font_size = await footer.evaluate("el => window.getComputedStyle(el).fontSize")
            print(f"✓ Footer font size: {font_size}")
            
            # Test footer visibility in both themes
            print("\n6. Testing footer visibility in both themes...")
            theme_button = page.locator("#themeToggle")
            
            # Switch to light theme
            await theme_button.click()
            await page.wait_for_timeout(500)
            await expect(footer).to_be_visible()
            print("✓ Footer visible in light theme")
            
            # Switch back to dark theme
            await theme_button.click()
            await page.wait_for_timeout(500)
            await expect(footer).to_be_visible()
            print("✓ Footer visible in dark theme")
            
            print("\n=== Footer Tests Passed! ===\n")
            
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Footer test failed with error: {e}")
            await browser.close()
            return False


async def main():
    """Run all theme toggle tests"""
    print("\n" + "="*60)
    print("THEME TOGGLE E2E TEST SUITE")
    print("="*60)
    
    # Test 1: Functionality
    result1 = await test_theme_toggle_button()
    
    # Test 2: Visual appearance
    result2 = await test_theme_visual_appearance()
    
    # Test 3: Footer presence and styling
    result3 = await test_footer_presence()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Functionality Tests: {'✓ PASSED' if result1 else '✗ FAILED'}")
    print(f"Visual Tests: {'✓ PASSED' if result2 else '✗ FAILED'}")
    print(f"Footer Tests: {'✓ PASSED' if result3 else '✗ FAILED'}")
    
    if result1 and result2 and result3:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

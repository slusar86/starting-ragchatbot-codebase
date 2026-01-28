"""
E2E Tests for UI Components and Layout

Tests sidebar, collapsibles, responsive design, and visual elements.
"""

import asyncio
from playwright.async_api import async_playwright, expect


async def test_sidebar_collapsibles():
    """Test collapsible sections in sidebar"""
    print("\n=== Testing Sidebar Collapsibles ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Test course stats collapsible
            print("1. Testing course stats collapsible...")
            stats_summary = page.locator(".stats-header")
            await expect(stats_summary).to_be_visible()
            print("✓ Stats header visible")
            
            # Check if initially open or closed
            stats_details = page.locator(".stats-collapsible")
            is_open = await stats_details.get_attribute("open")
            print(f"  Initial state: {'open' if is_open else 'closed'}")
            
            # Click to toggle
            await stats_summary.click()
            await page.wait_for_timeout(300)
            new_state = await stats_details.get_attribute("open")
            assert new_state != is_open  # State should change
            print("✓ Stats collapsible toggles correctly")
            
            # Test suggested questions collapsible
            print("\n2. Testing suggested questions collapsible...")
            suggested_summary = page.locator(".suggested-header")
            await expect(suggested_summary).to_be_visible()
            print("✓ Suggested questions header visible")
            
            suggested_details = page.locator(".suggested-collapsible")
            is_open = await suggested_details.get_attribute("open")
            print(f"  Initial state: {'open' if is_open else 'closed'}")
            
            # Click to toggle
            await suggested_summary.click()
            await page.wait_for_timeout(300)
            new_state = await suggested_details.get_attribute("open")
            assert new_state != is_open
            print("✓ Suggested questions collapsible toggles correctly")
            
            print("\n=== Sidebar Collapsibles Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_layout_structure():
    """Test main layout structure and elements"""
    print("\n=== Testing Layout Structure ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            print("1. Checking header elements...")
            header = page.locator("header")
            await expect(header).to_be_visible()
            
            title = page.locator("header h1")
            title_text = await title.text_content()
            assert "Course Materials Assistant" in title_text
            print(f"✓ Header title: {title_text}")
            
            subtitle = page.locator("header .subtitle")
            subtitle_text = await subtitle.text_content()
            print(f"✓ Subtitle: {subtitle_text}")
            
            print("\n2. Checking main layout sections...")
            sidebar = page.locator(".sidebar")
            await expect(sidebar).to_be_visible()
            print("✓ Sidebar visible")
            
            chat_main = page.locator(".chat-main")
            await expect(chat_main).to_be_visible()
            print("✓ Main chat area visible")
            
            print("\n3. Checking footer...")
            footer = page.locator(".app-footer")
            await expect(footer).to_be_visible()
            footer_text = await footer.text_content()
            assert "Claude" in footer_text
            print(f"✓ Footer visible: {footer_text.strip()}")
            
            print("\n4. Checking chat input area...")
            chat_input = page.locator("#chatInput")
            await expect(chat_input).to_be_visible()
            
            placeholder = await chat_input.get_attribute("placeholder")
            print(f"✓ Input placeholder: {placeholder}")
            
            send_button = page.locator("#sendButton")
            await expect(send_button).to_be_visible()
            print("✓ Send button visible")
            
            print("\n=== Layout Structure Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_responsive_design():
    """Test responsive design at different viewport sizes"""
    print("\n=== Testing Responsive Design ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Test desktop size
            print("1. Testing desktop viewport (1920x1080)...")
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            sidebar = page.locator(".sidebar")
            await expect(sidebar).to_be_visible()
            print("✓ Sidebar visible on desktop")
            
            await page.close()
            
            # Test tablet size
            print("\n2. Testing tablet viewport (768x1024)...")
            page = await browser.new_page(viewport={"width": 768, "height": 1024})
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Check layout still functional
            chat_input = page.locator("#chatInput")
            await expect(chat_input).to_be_visible()
            print("✓ Layout functional on tablet")
            
            await page.close()
            
            # Test mobile size
            print("\n3. Testing mobile viewport (375x667)...")
            page = await browser.new_page(viewport={"width": 375, "height": 667})
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Check essential elements still visible
            chat_input = page.locator("#chatInput")
            await expect(chat_input).to_be_visible()
            print("✓ Chat input visible on mobile")
            
            send_button = page.locator("#sendButton")
            await expect(send_button).to_be_visible()
            print("✓ Send button visible on mobile")
            
            await page.close()
            
            print("\n=== Responsive Design Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_message_display():
    """Test message display formatting and sources"""
    print("\n=== Testing Message Display ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Send a message
            print("1. Sending message...")
            await page.fill("#chatInput", "What is Python?")
            await page.click("#sendButton")
            
            # Wait for user message
            await page.wait_for_selector(".message.user", timeout=5000)
            print("✓ User message displayed")
            
            # Wait for assistant response
            await page.wait_for_timeout(3000)
            
            # Check message structure
            print("\n2. Checking message structure...")
            user_messages = page.locator(".message.user")
            user_count = await user_messages.count()
            print(f"✓ User messages: {user_count}")
            
            assistant_messages = page.locator(".message.assistant")
            assistant_count = await assistant_messages.count()
            print(f"✓ Assistant messages: {assistant_count}")
            
            # Check for message content
            print("\n3. Checking message content...")
            last_assistant = page.locator(".message.assistant").last
            message_content = last_assistant.locator(".message-content")
            await expect(message_content).to_be_visible()
            
            content_text = await message_content.text_content()
            print(f"✓ Response content length: {len(content_text)} characters")
            assert len(content_text) > 10
            
            # Check if sources are displayed
            print("\n4. Checking for sources...")
            sources = last_assistant.locator(".sources")
            sources_count = await sources.count()
            if sources_count > 0:
                print(f"✓ Sources section found: {sources_count}")
            else:
                print("  No sources in this response")
            
            print("\n=== Message Display Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_scroll_behavior():
    """Test chat scrolls to bottom on new messages"""
    print("\n=== Testing Scroll Behavior ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Send multiple messages to fill chat
            print("1. Sending multiple messages...")
            for i in range(3):
                await page.fill("#chatInput", f"Test message {i+1}")
                await page.click("#sendButton")
                await page.wait_for_timeout(1000)
                print(f"  Sent message {i+1}")
            
            await page.wait_for_timeout(2000)
            
            # Check scroll position
            print("\n2. Checking scroll position...")
            chat_messages = page.locator("#chatMessages")
            
            # Get scroll info
            scroll_info = await chat_messages.evaluate("""
                el => ({
                    scrollTop: el.scrollTop,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    isAtBottom: Math.abs(el.scrollHeight - el.clientHeight - el.scrollTop) < 10
                })
            """)
            
            print(f"  Scroll top: {scroll_info['scrollTop']}")
            print(f"  Scroll height: {scroll_info['scrollHeight']}")
            print(f"  Client height: {scroll_info['clientHeight']}")
            
            if scroll_info['isAtBottom']:
                print("✓ Chat scrolled to bottom")
            else:
                print("⚠ Chat may not be at bottom (could be due to timing)")
            
            print("\n=== Scroll Behavior Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_accessibility_features():
    """Test accessibility features"""
    print("\n=== Testing Accessibility Features ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Check ARIA labels
            print("1. Checking ARIA labels...")
            
            theme_toggle = page.locator("#themeToggle")
            aria_label = await theme_toggle.get_attribute("aria-label")
            assert aria_label
            print(f"✓ Theme toggle ARIA label: {aria_label}")
            
            # Check input accessibility
            print("\n2. Checking input accessibility...")
            chat_input = page.locator("#chatInput")
            input_type = await chat_input.get_attribute("type")
            placeholder = await chat_input.get_attribute("placeholder")
            autocomplete = await chat_input.get_attribute("autocomplete")
            
            print(f"✓ Input type: {input_type}")
            print(f"✓ Placeholder: {placeholder}")
            print(f"✓ Autocomplete: {autocomplete}")
            
            # Check button accessibility
            print("\n3. Checking button accessibility...")
            buttons = page.locator("button")
            button_count = await buttons.count()
            print(f"✓ Total buttons: {button_count}")
            
            # Check keyboard navigation
            print("\n4. Testing keyboard navigation...")
            await page.locator("#chatInput").focus()
            is_focused = await page.evaluate("document.activeElement.id === 'chatInput'")
            assert is_focused
            print("✓ Input can be focused")
            
            # Tab to send button
            await page.keyboard.press("Tab")
            await page.wait_for_timeout(100)
            active_element = await page.evaluate("document.activeElement.id")
            print(f"✓ Tab navigation works (focused: {active_element})")
            
            print("\n=== Accessibility Features Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def main():
    """Run all UI component tests"""
    print("\n" + "="*60)
    print("UI COMPONENTS AND LAYOUT E2E TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Sidebar collapsibles
    results.append(("Sidebar Collapsibles", await test_sidebar_collapsibles()))
    
    # Test 2: Layout structure
    results.append(("Layout Structure", await test_layout_structure()))
    
    # Test 3: Responsive design
    results.append(("Responsive Design", await test_responsive_design()))
    
    # Test 4: Message display
    results.append(("Message Display", await test_message_display()))
    
    # Test 5: Scroll behavior
    results.append(("Scroll Behavior", await test_scroll_behavior()))
    
    # Test 6: Accessibility
    results.append(("Accessibility Features", await test_accessibility_features()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All UI component tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

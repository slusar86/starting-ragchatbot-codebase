"""
E2E Tests for Chat Functionality

Tests core chat features including message sending, receiving, session management,
and error handling using Playwright.
"""

import asyncio
from playwright.async_api import async_playwright, expect


async def test_initial_page_load():
    """Test that page loads correctly with welcome message"""
    print("\n=== Testing Initial Page Load ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("1. Loading application...")
            await page.goto("http://localhost:8000", wait_until="networkidle")
            print("✓ Page loaded successfully")
            
            # Check welcome message appears
            print("\n2. Checking for welcome message...")
            welcome_msg = page.locator(".message.assistant .message-content").first
            await expect(welcome_msg).to_be_visible(timeout=5000)
            welcome_text = await welcome_msg.text_content()
            assert "Welcome" in welcome_text
            print(f"✓ Welcome message displayed: {welcome_text[:50]}...")
            
            # Check essential UI elements exist
            print("\n3. Checking UI elements...")
            await expect(page.locator("#chatInput")).to_be_visible()
            print("✓ Chat input visible")
            await expect(page.locator("#sendButton")).to_be_visible()
            print("✓ Send button visible")
            await expect(page.locator("#newChatButton")).to_be_visible()
            print("✓ New chat button visible")
            
            print("\n=== Initial Page Load Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_send_message():
    """Test sending a message and receiving a response"""
    print("\n=== Testing Send Message ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            print("1. Typing message...")
            test_message = "What courses are available?"
            await page.fill("#chatInput", test_message)
            print(f"✓ Typed message: {test_message}")
            
            # Count initial messages
            initial_count = await page.locator(".message").count()
            print(f"  Initial message count: {initial_count}")
            
            print("\n2. Sending message...")
            await page.click("#sendButton")
            print("✓ Send button clicked")
            
            # Wait for user message to appear
            print("\n3. Waiting for user message...")
            await page.wait_for_selector(".message.user", timeout=5000)
            user_msg = page.locator(".message.user").last
            user_text = await user_msg.text_content()
            assert test_message in user_text
            print(f"✓ User message displayed: {user_text}")
            
            # Wait for loading indicator
            print("\n4. Checking loading indicator...")
            try:
                loading = page.locator(".loading-dots")
                await expect(loading).to_be_visible(timeout=2000)
                print("✓ Loading indicator shown")
            except:
                print("⚠ Loading indicator not found (may have been too fast)")
            
            # Wait for assistant response
            print("\n5. Waiting for assistant response...")
            await page.wait_for_selector(".message.assistant:last-child:not(:has(.loading-dots))", timeout=10000)
            
            assistant_msg = page.locator(".message.assistant").last
            response_text = await assistant_msg.text_content()
            assert len(response_text) > 20  # Response should have content
            print(f"✓ Assistant response received: {response_text[:100]}...")
            
            # Check input is re-enabled and cleared
            print("\n6. Checking input state...")
            input_value = await page.input_value("#chatInput")
            assert input_value == ""
            print("✓ Input cleared after sending")
            
            is_disabled = await page.locator("#chatInput").is_disabled()
            assert not is_disabled
            print("✓ Input re-enabled")
            
            print("\n=== Send Message Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_new_chat_button():
    """Test new chat button clears chat and creates new session"""
    print("\n=== Testing New Chat Button ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Send a message first
            print("1. Sending initial message...")
            await page.fill("#chatInput", "Test message")
            await page.click("#sendButton")
            await page.wait_for_selector(".message.user", timeout=5000)
            print("✓ Initial message sent")
            
            # Wait for response
            await page.wait_for_timeout(2000)
            
            # Count messages before clearing
            message_count = await page.locator(".message").count()
            print(f"  Messages before clear: {message_count}")
            assert message_count >= 2  # At least welcome + user message
            
            # Click new chat
            print("\n2. Clicking new chat button...")
            await page.click("#newChatButton")
            await page.wait_for_timeout(1000)
            print("✓ New chat button clicked")
            
            # Check button feedback
            print("\n3. Checking button feedback...")
            button_text = await page.locator("#newChatButton").text_content()
            if "✓" in button_text or "STARTED" in button_text:
                print(f"✓ Button feedback shown: {button_text}")
            
            # Wait for button to reset
            await page.wait_for_timeout(2000)
            
            # Check messages cleared (only welcome message should remain)
            print("\n4. Checking chat cleared...")
            new_message_count = await page.locator(".message").count()
            print(f"  Messages after clear: {new_message_count}")
            assert new_message_count == 1  # Only welcome message
            print("✓ Chat history cleared")
            
            # Verify it's the welcome message
            first_msg = page.locator(".message").first
            msg_text = await first_msg.text_content()
            assert "Welcome" in msg_text
            print("✓ Welcome message displayed")
            
            print("\n=== New Chat Button Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_course_stats_loading():
    """Test course statistics load correctly"""
    print("\n=== Testing Course Stats Loading ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(2000)  # Wait for stats to load
            
            print("1. Checking course count...")
            total_courses = page.locator("#totalCourses")
            await expect(total_courses).to_be_visible()
            course_count = await total_courses.text_content()
            print(f"✓ Total courses: {course_count}")
            assert course_count != "-"  # Should be loaded
            assert course_count != "0"  # Should have courses
            
            print("\n2. Checking course titles...")
            course_titles = page.locator("#courseTitles")
            await expect(course_titles).to_be_visible()
            
            # Check if titles loaded (not loading message)
            titles_content = await course_titles.text_content()
            assert "Loading..." not in titles_content
            print(f"✓ Course titles loaded")
            
            # Count title items
            title_items = page.locator(".course-title-item")
            title_count = await title_items.count()
            print(f"  Number of course titles: {title_count}")
            assert title_count > 0
            
            # Print first few titles
            for i in range(min(3, title_count)):
                title = await title_items.nth(i).text_content()
                print(f"    - {title}")
            
            print("\n=== Course Stats Loading Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_suggested_questions():
    """Test suggested question buttons work"""
    print("\n=== Testing Suggested Questions ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            print("1. Finding suggested questions...")
            suggested_buttons = page.locator(".suggested-item")
            button_count = await suggested_buttons.count()
            print(f"✓ Found {button_count} suggested questions")
            assert button_count > 0
            
            # Get text from first button
            first_button = suggested_buttons.first
            button_text = await first_button.get_attribute("data-question")
            print(f"\n2. Testing button: '{button_text[:50]}...'")
            
            # Click first suggested question
            await first_button.click()
            await page.wait_for_timeout(500)
            
            # Check if input was populated
            print("\n3. Checking input populated...")
            input_value = await page.input_value("#chatInput")
            assert button_text in input_value
            print(f"✓ Input populated with: {input_value[:50]}...")
            
            # Message should be sent automatically
            print("\n4. Waiting for message to be sent...")
            await page.wait_for_selector(".message.user", timeout=5000)
            user_msg = page.locator(".message.user").last
            msg_text = await user_msg.text_content()
            assert button_text in msg_text
            print("✓ Message sent automatically")
            
            print("\n=== Suggested Questions Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_error_handling():
    """Test error handling when server is unavailable"""
    print("\n=== Testing Error Handling ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            # Mock network failure
            print("1. Setting up network failure simulation...")
            await page.route("**/api/query", lambda route: route.abort())
            print("✓ Network requests will be aborted")
            
            # Try to send a message
            print("\n2. Sending message with network failure...")
            await page.fill("#chatInput", "Test error handling")
            await page.click("#sendButton")
            
            # Wait for error message
            print("\n3. Waiting for error message...")
            await page.wait_for_timeout(2000)
            
            # Check for error in last assistant message
            last_message = page.locator(".message.assistant").last
            error_text = await last_message.text_content()
            assert "Error" in error_text or "failed" in error_text.lower()
            print(f"✓ Error message displayed: {error_text[:100]}")
            
            # Check input is re-enabled
            print("\n4. Checking input state after error...")
            is_disabled = await page.locator("#chatInput").is_disabled()
            assert not is_disabled
            print("✓ Input re-enabled after error")
            
            print("\n=== Error Handling Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def test_keyboard_enter():
    """Test Enter key sends message"""
    print("\n=== Testing Keyboard Enter ===\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            print("1. Typing message...")
            test_message = "Testing enter key"
            await page.fill("#chatInput", test_message)
            print(f"✓ Typed: {test_message}")
            
            # Focus input and press Enter
            print("\n2. Pressing Enter key...")
            await page.locator("#chatInput").press("Enter")
            print("✓ Enter key pressed")
            
            # Wait for user message
            print("\n3. Waiting for message to be sent...")
            await page.wait_for_selector(".message.user", timeout=5000)
            user_msg = page.locator(".message.user").last
            msg_text = await user_msg.text_content()
            assert test_message in msg_text
            print(f"✓ Message sent via Enter key: {msg_text}")
            
            print("\n=== Keyboard Enter Test Passed! ===\n")
            await page.wait_for_timeout(2000)
            await browser.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            await browser.close()
            return False


async def main():
    """Run all chat functionality tests"""
    print("\n" + "="*60)
    print("CHAT FUNCTIONALITY E2E TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Initial page load
    results.append(("Initial Page Load", await test_initial_page_load()))
    
    # Test 2: Send message
    results.append(("Send Message", await test_send_message()))
    
    # Test 3: New chat button
    results.append(("New Chat Button", await test_new_chat_button()))
    
    # Test 4: Course stats
    results.append(("Course Stats Loading", await test_course_stats_loading()))
    
    # Test 5: Suggested questions
    results.append(("Suggested Questions", await test_suggested_questions()))
    
    # Test 6: Error handling
    results.append(("Error Handling", await test_error_handling()))
    
    # Test 7: Keyboard enter
    results.append(("Keyboard Enter", await test_keyboard_enter()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All chat functionality tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

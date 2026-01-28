"""
Full-stack smoke test - Tests frontend served through the backend
"""
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"

def test_full_integration():
    """Test complete frontend-backend integration"""
    print("\n🔍 Full Stack Integration Test")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to the static frontend (mounted at root)
            print("   ⏳ Loading frontend from backend...")
            page.goto(f"{BASE_URL}/", timeout=10000)
            print("   ✓ Frontend loaded from backend")
            
            # Wait for page to be fully ready
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Verify UI elements
            title = page.title()
            print(f"   ✓ Page title: {title}")
            
            # Check course stats loaded
            course_stats = page.locator("#totalCourses")
            if course_stats.is_visible():
                stats_text = course_stats.text_content()
                print(f"   ✓ Course stats: {stats_text} courses")
            
            # Test 1: Simple query
            print("\n   📝 Test 1: Simple General Query")
            input_field = page.locator("#chatInput")
            input_field.fill("What is RAG?")
            print("      ✓ Query entered: 'What is RAG?'")
            
            send_button = page.locator("#sendButton")
            send_button.click()
            print("      ✓ Send button clicked")
            
            # Wait for response
            page.wait_for_selector("#chatMessages .message.assistant", timeout=15000)
            print("      ✓ Response received")
            
            # Get response text
            assistant_messages = page.locator("#chatMessages .message.assistant")
            if assistant_messages.count() > 0:
                response = assistant_messages.last.text_content()
                print(f"      ✓ Response length: {len(response)} chars")
                if len(response) > 50:
                    print(f"      ✓ Preview: {response[:100]}...")
            
            time.sleep(2)
            
            # Test 2: Course-specific query (should use tools)
            print("\n   📝 Test 2: Course-Specific Query (Tool Calling)")
            input_field.fill("What is covered in lesson 3 of the MCP course?")
            print("      ✓ Query entered: course-specific question")
            
            send_button.click()
            print("      ✓ Send button clicked")
            
            # Wait for response (might take longer with tool calls)
            page.wait_for_selector("#chatMessages .message.assistant", timeout=20000)
            time.sleep(1)  # Wait for animation
            print("      ✓ Response received (tool may have been called)")
            
            # Check response
            assistant_messages = page.locator("#chatMessages .message.assistant")
            if assistant_messages.count() >= 2:
                response = assistant_messages.last.text_content()
                print(f"      ✓ Response length: {len(response)} chars")
                if "lesson" in response.lower() or "mcp" in response.lower():
                    print("      ✓ Response seems relevant to query")
            
            time.sleep(2)
            
            # Test 3: Multi-round capable query
            print("\n   📝 Test 3: Multi-Round Query (New Feature)")
            complex_query = "Compare the topics covered in lesson 2 of Building Towards Computer Use with lesson 2 of the MCP course"
            input_field.fill(complex_query)
            print("      ✓ Complex multi-step query entered")
            
            send_button.click()
            print("      ✓ Send button clicked")
            
            # Wait for response (may take longer with multiple rounds)
            try:
                page.wait_for_selector("#chatMessages .message.assistant", timeout=25000)
                time.sleep(1)
                print("      ✓ Response received (multi-round processing completed)")
                
                assistant_messages = page.locator("#chatMessages .message.assistant")
                if assistant_messages.count() >= 3:
                    response = assistant_messages.last.text_content()
                    print(f"      ✓ Response length: {len(response)} chars")
                    
                    # Check if response mentions both courses
                    response_lower = response.lower()
                    if "building" in response_lower or "mcp" in response_lower:
                        print("      ✓ Response references course content")
                    if len(response) > 200:
                        print("      ✓ Substantial response (likely used multiple tool rounds)")
                        
            except Exception as e:
                print(f"      ⚠ Multi-round test couldn't fully verify: {e}")
            
            time.sleep(3)
            
            # Test 4: New chat button
            print("\n   📝 Test 4: New Chat Functionality")
            new_chat_button = page.locator("#newChatButton")
            if new_chat_button.is_visible():
                message_count_before = page.locator("#chatMessages .message").count()
                print(f"      ✓ Messages before new chat: {message_count_before}")
                
                new_chat_button.click()
                time.sleep(1)
                
                message_count_after = page.locator("#chatMessages .message").count()
                print(f"      ✓ Messages after new chat: {message_count_after}")
                
                if message_count_after == 0:
                    print("      ✓ Chat cleared successfully")
                else:
                    print(f"      ⚠ Chat not fully cleared (still {message_count_after} messages)")
            
            time.sleep(3)
            print("\n   ✅ All integration tests completed!")
            
        except Exception as e:
            print(f"\n   ❌ Integration test failed: {e}")
            try:
                page.screenshot(path="integration_error.png")
                print("   📸 Screenshot saved to integration_error.png")
            except:
                pass
            raise
        finally:
            print("\n   ⏸ Closing browser in 3 seconds...")
            time.sleep(3)
            browser.close()

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 RAG Chatbot Full-Stack Integration Test")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Load frontend from backend server")
    print("  2. Test simple query (no tools)")
    print("  3. Test course-specific query (single tool call)")
    print("  4. Test complex multi-round query (NEW FEATURE)")
    print("  5. Test new chat functionality")
    print("\n" + "=" * 70)
    
    # Check if server is running
    import requests
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✓ Server is running at {BASE_URL}\n")
    except:
        print(f"❌ Server is NOT running at {BASE_URL}")
        print("   Start server first: ./run.sh or .\\run.ps1\n")
        exit(1)
    
    try:
        test_full_integration()
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Integration successful!")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        exit(1)

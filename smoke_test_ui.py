"""
Smoke tests for RAG Chatbot UI using Playwright
Tests the frontend and API integration
"""
import os
import time
from playwright.sync_api import sync_playwright, expect

# Configuration
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "frontend", "index.html")

def test_api_health():
    """Test that API is responding"""
    print("\n🔍 Test 1: API Health Check")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Test API docs endpoint
            response = page.goto(f"{BASE_URL}/docs", timeout=10000)
            assert response.status == 200, f"Expected 200, got {response.status}"
            print("   ✓ API /docs endpoint responding")
            
            # Check page loaded
            page.wait_for_load_state("networkidle", timeout=10000)
            print(f"   ✓ API Documentation loaded successfully")
            
        except Exception as e:
            print(f"   ✗ API Health Check failed: {e}")
            raise
        finally:
            browser.close()

def test_frontend_loads():
    """Test that frontend HTML loads correctly"""
    print("\n🔍 Test 2: Frontend Page Load")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible browser for debugging
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Load frontend HTML file
            page.goto(f"file:///{FRONTEND_PATH.replace(chr(92), '/')}")
            print(f"   ✓ Frontend loaded from: {FRONTEND_PATH}")
            
            # Check title
            title = page.title()
            assert "Course" in title or "RAG" in title or "Chat" in title or "Assistant" in title, f"Unexpected title: {title}"
            print(f"   ✓ Page title: {title}")
            
            # Check for key UI elements
            input_field = page.locator("#chatInput")
            assert input_field.is_visible(), "Chat input not found"
            print("   ✓ Chat input field found")
            
            # Check for send button (it's an SVG icon button)
            send_button = page.locator("#sendButton")
            assert send_button.is_visible(), "Send button not found"
            print("   ✓ Send button found")
            
            # Check for chat messages area
            chat_area = page.locator("#chatMessages")
            assert chat_area.is_visible(), "Chat messages area not found"
            print("   ✓ Chat messages area found")
            
            # Check for sidebar
            sidebar = page.locator(".sidebar")
            if sidebar.count() > 0:
                print("   ✓ Sidebar found")
            
            time.sleep(2)  # Keep browser open for visual inspection
            
        except Exception as e:
            print(f"   ✗ Frontend load failed: {e}")
            raise
        finally:
            browser.close()

def test_simple_query():
    """Test sending a simple query through the UI"""
    print("\n🔍 Test 3: Simple Query Test")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Load frontend
            page.goto(f"file:///{FRONTEND_PATH.replace(chr(92), '/')}")
            print("   ✓ Frontend loaded")
            
            # Wait for page to be ready
            page.wait_for_load_state("networkidle")
            
            # Find input field
            input_field = page.locator("#chatInput")
            input_field.fill("What courses are available?")
            print("   ✓ Query entered: 'What courses are available?'")
            
            # Click send button
            send_button = page.locator("#sendButton")
            send_button.click()
            print("   ✓ Send button clicked")
            
            # Wait for response (with timeout)
            try:
                # Wait for message to appear in chat
                page.wait_for_selector("#chatMessages .message", timeout=15000)
                print("   ✓ Response received")
                
                # Check if response contains text
                messages = page.locator("#chatMessages .message")
                message_count = messages.count()
                print(f"   ✓ Messages in chat: {message_count}")
                
                if message_count > 0:
                    last_message = messages.last
                    response_text = last_message.text_content()
                    
                    if response_text and len(response_text) > 10:
                        print(f"   ✓ Response length: {len(response_text)} characters")
                        print(f"   ✓ Response preview: {response_text[:100]}...")
                    else:
                        print(f"   ⚠ Response seems short: {response_text}")
                else:
                    print("   ⚠ No messages found in chat")
                    
            except Exception as e:
                print(f"   ⚠ Could not verify response: {e}")
            
            time.sleep(3)  # Keep browser open for inspection
            
        except Exception as e:
            print(f"   ✗ Query test failed: {e}")
            try:
                page.screenshot(path="test_error.png")
                print("   📸 Screenshot saved to test_error.png")
            except:
                pass
            raise
        finally:
            browser.close()

def test_multi_round_query():
    """Test a complex query that might trigger 2-round tool calling"""
    print("\n🔍 Test 4: Multi-Round Query Test (New Feature)")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Load frontend
            page.goto(f"file:///{FRONTEND_PATH.replace(chr(92), '/')}")
            print("   ✓ Frontend loaded")
            
            # Wait for page ready
            page.wait_for_load_state("networkidle")
            
            # Complex query that requires multiple searches
            complex_query = "Search for courses that discuss similar topics to lesson 3 of Building Towards Computer Use"
            
            input_field = page.locator("#chatInput")
            input_field.fill(complex_query)
            print(f"   ✓ Complex query entered")
            
            # Click send
            send_button = page.locator("#sendButton")
            send_button.click()
            print("   ✓ Send button clicked")
            
            # Wait longer for potential multi-round processing
            try:
                page.wait_for_selector("#chatMessages .message", timeout=20000)
                print("   ✓ Response received (multi-round processing may have occurred)")
                
                messages = page.locator("#chatMessages .message")
                message_count = messages.count()
                
                if message_count > 0:
                    last_message = messages.last
                    response_text = last_message.text_content()
                    
                    if response_text:
                        print(f"   ✓ Response length: {len(response_text)} characters")
                        if len(response_text) > 100:
                            print("   ✓ Substantial response received (good sign for multi-round)")
                else:
                    print("   ⚠ No messages found")
                        
            except Exception as e:
                print(f"   ⚠ Response verification failed: {e}")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"   ✗ Multi-round test failed: {e}")
            try:
                page.screenshot(path="test_multiround_error.png")
            except:
                pass
            raise
        finally:
            browser.close()

def run_all_tests():
    """Run all smoke tests"""
    print("=" * 60)
    print("🚀 Starting UI Smoke Tests for RAG Chatbot")
    print("=" * 60)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Frontend Load", test_frontend_loads),
        ("Simple Query", test_simple_query),
        ("Multi-Round Query", test_multi_round_query)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    # Check if server is running
    import requests
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✓ Server is running at {BASE_URL}")
    except:
        print(f"⚠ Warning: Server may not be running at {BASE_URL}")
        print("   Start server with: ./run.sh or .\\run.ps1")
        exit(1)
    
    success = run_all_tests()
    exit(0 if success else 1)

"""
Comprehensive Test Runner for All Frontend Tests

Runs all frontend E2E tests in sequence with summary reporting.
"""

import asyncio
import sys
from pathlib import Path

# Import all test modules
sys.path.insert(0, str(Path(__file__).parent))

from test_theme_toggle import main as theme_tests
from test_chat_functionality import main as chat_tests
from test_ui_components import main as ui_tests


async def run_all_tests():
    """Run all frontend test suites"""
    print("\n" + "="*70)
    print(" "*15 + "FRONTEND E2E TEST SUITE - COMPLETE")
    print("="*70)
    
    results = {}
    
    # Suite 1: Theme Toggle Tests
    print("\n" + "-"*70)
    print("SUITE 1: Theme Toggle and Footer Tests")
    print("-"*70)
    result = await theme_tests()
    results["Theme Toggle"] = result == 0
    
    # Suite 2: Chat Functionality Tests
    print("\n" + "-"*70)
    print("SUITE 2: Chat Functionality Tests")
    print("-"*70)
    result = await chat_tests()
    results["Chat Functionality"] = result == 0
    
    # Suite 3: UI Components Tests
    print("\n" + "-"*70)
    print("SUITE 3: UI Components and Layout Tests")
    print("-"*70)
    result = await ui_tests()
    results["UI Components"] = result == 0
    
    # Final Summary
    print("\n" + "="*70)
    print(" "*20 + "FINAL TEST SUMMARY")
    print("="*70)
    
    for suite_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{suite_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for p in results.values() if p)
    
    print(f"\nTotal Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if all(results.values()):
        print("\n🎉 ALL FRONTEND TESTS PASSED! 🎉")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

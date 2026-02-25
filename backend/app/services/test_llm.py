"""
Comprehensive LLM service tests

Tests various prompt types and edge cases to ensure robust LLM integration.
"""

from .llm import get_llm_service
from ..models.llm import RoutingPreferences
import time


def test_basic_prompts():
    """Test basic routing prompts"""
    print("="*70)
    print("TEST SUITE 1: BASIC PROMPTS")
    print("="*70)
    
    llm = get_llm_service()
    
    test_cases = [
        {
            "prompt": "scenic run avoiding highways",
            "expected_keys": ["highway", "scenic"],
            "expected_avoids": ["highway"],
            "expected_prefers": ["scenic"]
        },
        {
            "prompt": "night run on well-lit streets",
            "expected_keys": ["unlit"],
            "expected_avoids": ["unlit"],
            "expected_prefers": []
        },
        {
            "prompt": "quiet morning jog through neighborhoods",
            "expected_keys": ["residential"],
            "expected_avoids": [],
            "expected_prefers": ["residential"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {case['prompt']}")
        print('='*70)
        
        start_time = time.time()
        prefs = llm.analyze_prompt(case['prompt'])
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Response time: {elapsed:.2f}s")
        
        print(f"\n📊 Preferences:")
        for key, value in prefs.preferences.items():
            if value > 1.0:
                direction = f"AVOID (×{value})"
            elif value < 1.0:
                direction = f"PREFER (×{value})"
            else:
                direction = "NEUTRAL"
            print(f"   {key:15s}: {value:6.1f}  {direction}")
        
        print(f"\n💭 Reasoning:")
        print(f"   {prefs.reasoning}")
        
        # Validation
        print(f"\n✓ Validation:")
        for key in case['expected_keys']:
            if key in prefs.preferences:
                print(f"   ✅ Found expected key: {key}")
            else:
                print(f"   ⚠️  Missing expected key: {key}")
        
        print(f"\n" + "="*70)


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*70)
    print("TEST SUITE 2: EDGE CASES")
    print("="*70)
    
    llm = get_llm_service()
    
    edge_cases = [
        "run",  # Minimal prompt
        "I want to go running outside maybe near some trees and stuff and avoid cars",  # Long/vague
        "🏃‍♂️ scenic 🌳",  # Emojis
        "",  # Empty (will use fallback)
    ]
    
    for i, prompt in enumerate(edge_cases, 1):
        print(f"\n{'='*70}")
        print(f"Edge Case {i}: '{prompt}'")
        print('='*70)
        
        try:
            prefs = llm.analyze_prompt(prompt)
            print(f"\n📊 Preferences: {prefs.preferences}")
            print(f"💭 Reasoning: {prefs.reasoning}")
            print("✅ Handled successfully")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_consistency():
    """Test if same prompt gives consistent results"""
    print("\n" + "="*70)
    print("TEST SUITE 3: CONSISTENCY CHECK")
    print("="*70)
    
    llm = get_llm_service()
    prompt = "scenic run avoiding highways"
    
    results = []
    for i in range(3):
        print(f"\nRun {i+1}/3...")
        prefs = llm.analyze_prompt(prompt)
        results.append(prefs.preferences)
        print(f"   Result: {prefs.preferences}")
    
    print(f"\n📊 Analysis:")
    # Check if key preferences are present in all runs
    common_keys = set(results[0].keys())
    for result in results[1:]:
        common_keys &= set(result.keys())
    
    print(f"   Common keys across all runs: {common_keys}")
    
    # Check value ranges
    for key in common_keys:
        values = [r[key] for r in results]
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        print(f"   {key}: avg={avg:.1f}, variance={variance:.2f}")


def test_performance():
    """Test performance characteristics"""
    print("\n" + "="*70)
    print("TEST SUITE 4: PERFORMANCE")
    print("="*70)
    
    llm = get_llm_service()
    
    prompts = [
        "scenic run",
        "night run on lit streets",
        "avoid highways"
    ]
    
    times = []
    for prompt in prompts:
        start = time.time()
        prefs = llm.analyze_prompt(prompt)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"   '{prompt}': {elapsed:.2f}s")
    
    print(f"\n📊 Statistics:")
    print(f"   Average: {sum(times)/len(times):.2f}s")
    print(f"   Min: {min(times):.2f}s")
    print(f"   Max: {max(times):.2f}s")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🧪 " + "="*68 + " 🧪")
    print("STRIDER LLM SERVICE - COMPREHENSIVE TEST SUITE")
    print("🧪 " + "="*68 + " 🧪\n")
    
    try:
        test_basic_prompts()
        test_edge_cases()
        test_consistency()
        test_performance()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
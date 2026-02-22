"""
test llm service to verify ollama integration
"""

from llm import get_llm_service

def test_llm_service():

    print("="*70)
    print("TESTING LLM SERVICE")
    print("="*70)

    # Get LLM service
    llm = get_llm_service()

    # Test prompts
    test_cases = [
        "scenic run avoiding highways",
        "quiet morning jog through neighborhoods",
        "night run on well-lit streets only",
        "trail run through nature",
        "fast run on main roads",
        "peaceful evening run avoiding traffic"
    ]

    for i, prompt in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {prompt}")
        print('='*70)

    try:
    # Analyze prompt
        prefs = llm.analyze_prompt(prompt)

        print(f"\n📊 Preferences:")
        for key, value in prefs.preferences.items():
            if value > 1.0:
                direction = f"AVOID (×{value})"
            elif value < 1.0:
                direction = f"PREFER (×{value})"
            else:
                direction = "NEUTRAL"
            print(f" {key:15s}: {value:6.1f} {direction}")

        print(f"\n💭 Reasoning:")
        print(f" {prefs.reasoning}")

        if prefs.time_of_day:
            print(f"\n🕐 Time: {prefs.time_of_day}")

        if prefs.distance_preference:
            print(f"\n📏 Distance: {prefs.distance_preference}")

    except Exception as e:
        print(f"\nError: {e}")

        print(f"\n{'='*70}")
        print("SUCCESS - LLM SERVICE TESTS COMPLETE")
        print("="*70)


if __name__ == "__main__":
    test_llm_service()
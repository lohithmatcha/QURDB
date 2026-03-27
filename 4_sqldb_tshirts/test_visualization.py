"""
Quick test script to verify visualization is working
"""
import sys
from visualization_helper import format_with_chart

# Test cases
test_cases = [
    # Single value
    ([(98,)], "How many Nike shirts?"),
    
    # Multiple columns
    ([('Nike', 98), ('Adidas', 120), ('Levi', 85)], "Compare stock by brand"),
    
    # List of values
    ([98, 120, 85], "Show me the stock values")
]

print("Testing Visualization Helper...")
print("=" * 50)

for i, (test_data, question) in enumerate(test_cases, 1):
    print(f"\nTest Case {i}: {question}")
    print(f"Input data: {test_data}")
    
    try:
        result = format_with_chart(question, test_data)
        print(f"✓ Chart Type: {result.get('chart_type')}")
        print(f"✓ Has Chart: {result.get('chart') is not None}")
        print(f"✓ Metadata: {result.get('metadata')}")
        if result.get('error'):
            print(f"✗ Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 50)
print("Testing complete! If you see any errors above, that's likely the issue.")


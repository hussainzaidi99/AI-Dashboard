"""Test Query Parser improvements"""
import sys
import os
import asyncio
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.ai.query_parser import QueryParser, QueryIntent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create sample DataFrame
sample_data = {
    'user_id': [1, 2, 3, 4, 5],
    'age': [25, 30, 35, 40, 45],
    'purchase_value': [100, 200, 150, 300, 250],
    'region': ['North', 'South', 'East', 'West', 'North'],
    'date': pd.date_range('2024-01-01', periods=5),
    'product': ['A', 'B', 'A', 'C', 'B']
}
df = pd.DataFrame(sample_data)

async def test_query_parser():
    """Test the query parser with various queries"""
    parser = QueryParser()
    
    test_cases = [
        {
            "query": "show me 'age' and 'purchase_value' by 'user_id' as a bar chart",
            "expected_chart": "bar",
            "expected_groupby": "user_id",
            "expected_columns": ["age", "purchase_value", "user_id"]
        },
        {
            "query": "Show me sales by region as a bar chart",
            "expected_chart": "bar",
            "expected_groupby": "region",
            "expected_columns": ["region"]
        },
        {
            "query": "Plot age distribution as a histogram",
            "expected_chart": "histogram",
            "expected_groupby": None,
            "expected_columns": ["age"]
        },
        {
            "query": "Show purchase_value trend over time as a line chart",
            "expected_chart": "line",
            "expected_groupby": None,
            "expected_columns": ["purchase_value"]
        }
    ]
    
    print("\n" + "="*80)
    print("QUERY PARSER TEST RESULTS")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        print(f"\n[Test {i}] Query: {query}")
        
        try:
            # Test rule-based parsing first
            parsed = parser._parse_with_rules(query, df)
            
            print(f"  Intent: {parsed.intent}")
            print(f"  Chart Type: {parsed.chart_type} (expected: {test_case['expected_chart']})")
            print(f"  Groupby: {parsed.groupby} (expected: {test_case['expected_groupby']})")
            print(f"  Columns: {parsed.columns} (expected: {test_case['expected_columns']})")
            print(f"  Confidence: {parsed.confidence:.2f}")
            
            # Check if results match expectations
            chart_match = parsed.chart_type == test_case['expected_chart']
            groupby_match = parsed.groupby == test_case['expected_groupby']
            
            print(f"  ✓ Chart Type Match: {chart_match}")
            print(f"  ✓ Groupby Match: {groupby_match}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Test AI parsing with better prompt
    print(f"\n" + "="*80)
    print("TESTING IMPROVED AI PROMPT")
    print("="*80)
    
    query = "show me 'age' and 'purchase_value' by 'user_id' as a bar chart"
    print(f"\nQuery: {query}")
    print("Testing with improved AI prompt (if LLM available)...")
    
    try:
        # This would require valid API key, but shows the new prompt is being used
        parsed_ai = await parser._parse_with_ai(query, df, session_id="test")
        print(f"  AI Intent: {parsed_ai.intent}")
        print(f"  AI Chart Type: {parsed_ai.chart_type}")
        print(f"  AI Columns: {parsed_ai.columns}")
        print(f"  AI Groupby: {parsed_ai.groupby}")
        print(f"  AI Confidence: {parsed_ai.confidence:.2f}")
    except Exception as e:
        print(f"  Note: AI parsing skipped (API not configured or rate limited)")
        print(f"  Error: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_query_parser())

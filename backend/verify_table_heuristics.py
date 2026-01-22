import sys
import os
import pandas as pd
from io import StringIO

# Add project root to path
sys.path.append(os.getcwd())

from app.core.processors.base import BaseProcessor

class MockProcessor(BaseProcessor):
    def process(self, file_path, **kwargs):
        pass

def test_stricter_table_detection():
    processor = MockProcessor()
    
    # 1. Test a clear table (Should pass)
    table_text = """Name,Age,City
Alice,25,New York
Bob,30,London
Charlie,35,Paris"""
    dfs = processor.extract_tables_from_text(table_text)
    print(f"Table Detection Test 1 (Clear Table): {'Passed' if len(dfs) == 1 else 'Failed'} (Found {len(dfs)})")
    
    # 2. Test a conversational text with commas (Should NOT be detected as table)
    conversational_text = """This is a sample sentence, it contains commas, and should not be a table.
Another sentence has, more commas, but it's just text.
Even a third sentence, with commas, isn't tabular data."""
    dfs = processor.extract_tables_from_text(conversational_text)
    print(f"Table Detection Test 2 (Conversational Text): {'Passed' if len(dfs) == 0 else 'Failed'} (Found {len(dfs)})")
    
    # 3. Test a inconsistent separator count (Should NOT be detected as table)
    inconsistent_text = """Column1,Column2,Column3
Row1,Data1
Row2,Data2,Extra,Data
Row3,Data3"""
    dfs = processor.extract_tables_from_text(inconsistent_text)
    print(f"Table Detection Test 3 (Inconsistent Structure): {'Passed' if len(dfs) == 0 else 'Failed'} (Found {len(dfs)})")

    # 4. Test a "Table" with only 2 rows (Should NOT be detected due to min rows=3)
    small_text = """Header,Value
Data1,100"""
    dfs = processor.extract_tables_from_text(small_text)
    print(f"Table Detection Test 4 (Small Table < 3 rows): {'Passed' if len(dfs) == 0 else 'Failed'} (Found {len(dfs)})")

if __name__ == "__main__":
    test_stricter_table_detection()

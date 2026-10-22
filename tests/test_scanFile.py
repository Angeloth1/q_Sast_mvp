from pathlib import Path
from analyzer import scan_file

TARGET = Path(__file__).parent.parent/"scripts"/"target.py"

def test_finds_all_five_calls():
    flags = scan_file(TARGET)
    assert len(flags) == 5 
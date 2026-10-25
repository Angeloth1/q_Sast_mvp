from pathlib import Path
from analyzer import scan_file
import pytest

TARGET = Path(__file__).parent.parent/"script"/"target.py"

def test_keyword_key_size_is_read(tmp_path):
    sample = tmp_path/"sample.py"
    sample.write_text("rsa.generate_private_key(public_exponent=65537, key_size=2048)")
    flags = scan_file(sample)
    assert len(flags) == 1 
    assert flags[0]["key_bits"]==2048

def test_positional_key_size_is_read(tmp_path):
    sample = tmp_path/"sample.py"
    sample.write_text("rsa.generate_private_key(65537, 4096)")
    flags = scan_file(sample)
    assert len(flags) == 1 
    assert flags[0]["key_bits"]== 4096

def test_missing_key_size_is_none(tmp_path):
    sample = tmp_path/"sample.py"
    sample.write_text("rsa.generate_private_key(65537,)")
    flags = scan_file(sample)
    assert len(flags) == 1 
    assert flags[0]["key_bits"] is None


def test_variable_key_size_is_read(tmp_path):
    sample = tmp_path/"sample.py"
    sample.write_text("KEY_SIZE=2048\nrsa.generate_private_key(65537, KEY_SIZE)")
    flags = scan_file(sample)
    assert len(flags) == 1 
    assert flags[0]["key_bits"]== 2048
    
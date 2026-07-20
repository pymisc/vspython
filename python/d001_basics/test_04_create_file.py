import datetime
import os
from unittest.mock import patch, mock_open

# Import your function dynamically to avoid folder path import issues
import importlib.util
spec = importlib.util.spec_from_file_location("create_file_module", "python/d001_basics/04_create_file.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
append_current_time = module.append_current_time

# --- TEST 1: File DOES NOT exist ---
@patch('datetime.datetime')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
def test_file_not_exists(mock_exists, mock_file, mock_datetime):
    # Setup: Tell our mock that the file does NOT exist
    mock_exists.return_value = False
    
    # Setup: Freeze time
    mock_datetime.now.return_value = datetime.datetime(2026, 7, 20, 12, 0, 0)
    
    # Action: Run the function
    append_current_time("dummy.txt")
    
    # Assertions: Did it do what we expected?
    mock_exists.assert_called_once_with("dummy.txt")
    mock_file.assert_called_once_with("dummy.txt", mode='a')
    mock_file().write.assert_called_once_with("2026-07-20 12:00:00\n")


# --- TEST 2: File DOES exist ---
@patch('datetime.datetime')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
def test_file_exists(mock_exists, mock_file, mock_datetime):
    # Setup: Tell our mock that the file DOES exist
    mock_exists.return_value = True
    
    # Setup: Freeze time
    mock_datetime.now.return_value = datetime.datetime(2026, 7, 20, 12, 0, 0)
    
    # Action: Run the function
    append_current_time("dummy.txt")
    
    # Assertions: Did it do what we expected?
    mock_exists.assert_called_once_with("dummy.txt")
    mock_file.assert_called_once_with("dummy.txt", mode='a')
    mock_file().write.assert_called_once_with("2026-07-20 12:00:00\n")

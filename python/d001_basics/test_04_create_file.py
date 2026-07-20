import os
import runpy
from unittest.mock import patch, mock_open, MagicMock

# Import your function dynamically
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
    
    # THE FIX: Create a mock for 'now' and force 'strftime' to return our exact string
    mock_now = MagicMock()
    mock_now.strftime.return_value = "2026-07-20 12:00:00"
    mock_datetime.now.return_value = mock_now
    
    # Action: Run the function
    append_current_time("dummy.txt")
    
    # Assertions
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
    
    # THE FIX: Apply the same mock configuration here
    mock_now = MagicMock()
    mock_now.strftime.return_value = "2026-07-20 12:00:00"
    mock_datetime.now.return_value = mock_now
    
    # Action: Run the function
    append_current_time("dummy.txt")
    
    # Assertions
    mock_exists.assert_called_once_with("dummy.txt")
    mock_file.assert_called_once_with("dummy.txt", mode='a')
    mock_file().write.assert_called_once_with("2026-07-20 12:00:00\n")

# --- TEST 3: The __main__ block ---
@patch('datetime.datetime')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
def test_main_execution(mock_exists, mock_file, mock_datetime):
    # Setup our mocks so the script doesn't actually write a file during the test
    mock_exists.return_value = True
    mock_now = MagicMock()
    mock_now.strftime.return_value = "2026-07-20 12:00:00"
    mock_datetime.now.return_value = mock_now
    
    # THE FIX: runpy.run_path executes the script and we force run_name="__main__"
    runpy.run_path("python/d001_basics/04_create_file.py", run_name="__main__")
    
    # Assert that the function was called with the hardcoded "testfile01.txt"
    mock_file.assert_called_once_with("testfile01.txt", mode='a')

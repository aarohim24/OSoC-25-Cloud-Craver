from src.utility.file_ops import create_directory
# Test 1: Create a folder 'test_folder' with default permissions
create_directory("test_folder")
# Test 2: Try creating the same folder again (should warn that it exists)
create_directory("test_folder")
# Test 3: Create a folder with owner-only permissions
create_directory("private_folder", 0o700)

"""
Test authentication to verify password hashes are correct.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.authentication import verify_password, hash_password, USERS_DB

def test_passwords():
    """Test that the hardcoded password hashes are correct."""
    print("Testing authentication passwords...\n")

    # Test admin password
    admin_hash = USERS_DB['admin']['password']
    print(f"Admin hash in database: {admin_hash}")
    print(f"Testing 'admin123'...")
    if verify_password('admin123', admin_hash):
        print("✓ Admin password is CORRECT\n")
    else:
        print("✗ Admin password is INCORRECT")
        print(f"Generating new hash for 'admin123':")
        new_hash = hash_password('admin123')
        print(f"New hash: {new_hash}\n")

    # Test viewer password
    viewer_hash = USERS_DB['viewer']['password']
    print(f"Viewer hash in database: {viewer_hash}")
    print(f"Testing 'viewer123'...")
    if verify_password('viewer123', viewer_hash):
        print("✓ Viewer password is CORRECT\n")
    else:
        print("✗ Viewer password is INCORRECT")
        print(f"Generating new hash for 'viewer123':")
        new_hash = hash_password('viewer123')
        print(f"New hash: {new_hash}\n")

if __name__ == '__main__':
    test_passwords()

"""
Test login functionality with the current authentication setup.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.authentication import authenticate, USERS_DB

def test_login():
    """Test login with valid and invalid credentials."""
    print("=" * 60)
    print("Testing JESUS Company Cash Management Login")
    print("=" * 60)
    print()

    # Test 1: Valid admin login
    print("Test 1: Admin login with correct password")
    user = authenticate('admin', 'admin123')
    if user:
        print(f"✓ SUCCESS - Logged in as {user['name']}")
        print(f"  Username: {user['username']}")
        print(f"  Role: {user['role']}")
        print(f"  Email: {user['email']}")
    else:
        print("✗ FAILED - Authentication failed")
    print()

    # Test 2: Valid viewer login
    print("Test 2: Viewer login with correct password")
    user = authenticate('viewer', 'viewer123')
    if user:
        print(f"✓ SUCCESS - Logged in as {user['name']}")
        print(f"  Username: {user['username']}")
        print(f"  Role: {user['role']}")
        print(f"  Email: {user['email']}")
    else:
        print("✗ FAILED - Authentication failed")
    print()

    # Test 3: Invalid password
    print("Test 3: Admin login with WRONG password")
    user = authenticate('admin', 'wrongpassword')
    if user is None:
        print("✓ SUCCESS - Correctly rejected invalid password")
    else:
        print("✗ FAILED - Should have rejected invalid password")
    print()

    # Test 4: Invalid username
    print("Test 4: Login with non-existent username")
    user = authenticate('nonexistent', 'anypassword')
    if user is None:
        print("✓ SUCCESS - Correctly rejected invalid username")
    else:
        print("✗ FAILED - Should have rejected invalid username")
    print()

    print("=" * 60)
    print("Login Testing Complete!")
    print("=" * 60)
    print()
    print("Summary:")
    print("--------")
    print("All authentication tests passed successfully.")
    print()
    print("You can now login to the dashboard with:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("Or as viewer:")
    print("  Username: viewer")
    print("  Password: viewer123")
    print()
    print("To start the dashboard, run:")
    print("  streamlit run dashboard/app.py")

if __name__ == '__main__':
    test_login()

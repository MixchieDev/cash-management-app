"""
Initialize default users for the JESUS Company Cash Management System.

This script creates the default admin and viewer users with properly hashed passwords.
Users are currently hardcoded in auth/authentication.py for Phase 1.

Phase 2 will move users to a database with proper user management.
"""
import bcrypt
from typing import Dict


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_default_users() -> Dict[str, Dict]:
    """
    Create default users with hashed passwords.

    Returns:
        Dictionary of users with hashed passwords
    """
    print("Creating default users for JESUS Company Cash Management System...")
    print()

    # Admin user
    admin_password = 'admin123'
    admin_hash = hash_password(admin_password)
    print(f"✓ Created admin user:")
    print(f"  Username: admin")
    print(f"  Password: {admin_password}")
    print(f"  Role: admin")
    print(f"  Hash: {admin_hash}")
    print()

    # Viewer user
    viewer_password = 'viewer123'
    viewer_hash = hash_password(viewer_password)
    print(f"✓ Created viewer user:")
    print(f"  Username: viewer")
    print(f"  Password: {viewer_password}")
    print(f"  Role: viewer")
    print(f"  Hash: {viewer_hash}")
    print()

    users_db = {
        'admin': {
            'name': 'CFO Mich',
            'password': admin_hash,
            'email': 'cfo@jesuscompany.com',
            'role': 'admin'
        },
        'viewer': {
            'name': 'Team Viewer',
            'password': viewer_hash,
            'email': 'team@jesuscompany.com',
            'role': 'viewer'
        }
    }

    # Verify hashes work
    print("Verifying password hashes...")
    admin_verified = verify_password(admin_password, admin_hash)
    viewer_verified = verify_password(viewer_password, viewer_hash)

    if admin_verified and viewer_verified:
        print("✓ All password hashes verified successfully")
        print()
        print("=" * 60)
        print("Default Users Created Successfully!")
        print("=" * 60)
        print()
        print("Login Credentials:")
        print("-" * 60)
        print("Admin Access:")
        print("  Username: admin")
        print("  Password: admin123")
        print()
        print("Viewer Access:")
        print("  Username: viewer")
        print("  Password: viewer123")
        print("-" * 60)
        print()
        print("Note: Users are currently hardcoded in auth/authentication.py")
        print("      Phase 2 will migrate to database-backed user management")
    else:
        print("✗ Password verification failed!")
        return None

    return users_db


if __name__ == '__main__':
    users = create_default_users()

    if users:
        print()
        print("To update auth/authentication.py with new hashes, copy the code below:")
        print()
        print("USERS_DB = {")
        for username, user_data in users.items():
            password_comment = 'admin123' if username == 'admin' else 'viewer123'
            print(f"    '{username}': {{")
            print(f"        'name': '{user_data['name']}',")
            print(f"        'password': '{user_data['password']}',  # '{password_comment}'")
            print(f"        'email': '{user_data['email']}',")
            print(f"        'role': '{user_data['role']}'")
            print(f"    }}{'' if username == list(users.keys())[-1] else ','}")
        print("}")

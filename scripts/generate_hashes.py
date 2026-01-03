"""
Generate correct bcrypt password hashes for default users.
"""
import bcrypt

def generate_hash(password: str) -> str:
    """Generate a bcrypt hash for a password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("Generating password hashes for default users...\n")

admin_hash = generate_hash('admin123')
viewer_hash = generate_hash('viewer123')

print(f"Admin password hash for 'admin123':")
print(f"'{admin_hash}'")
print()
print(f"Viewer password hash for 'viewer123':")
print(f"'{viewer_hash}'")
print()

# Verify they work
print("Verifying hashes...")
admin_verified = bcrypt.checkpw('admin123'.encode('utf-8'), admin_hash.encode('utf-8'))
viewer_verified = bcrypt.checkpw('viewer123'.encode('utf-8'), viewer_hash.encode('utf-8'))

print(f"Admin hash verification: {'✓ PASS' if admin_verified else '✗ FAIL'}")
print(f"Viewer hash verification: {'✓ PASS' if viewer_verified else '✗ FAIL'}")

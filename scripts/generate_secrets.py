#!/usr/bin/env python3
"""
Generate secure secrets for Flask application configuration.

This script generates cryptographically secure random values for:
- SECRET_KEY: Used for session management, CSRF protection, and signing cookies
- SECURITY_PASSWORD_SALT: Used for password hashing

Usage:
    python scripts/generate_secrets.py

The output can be copied directly into a .env file.
"""

import secrets

def generate_secret_key():
    """Generate a secure SECRET_KEY using cryptographically secure random bytes."""
    # 32 bytes = 256 bits, which is recommended for Flask SECRET_KEY
    return secrets.token_urlsafe(32)

def generate_password_salt():
    """Generate a secure SECURITY_PASSWORD_SALT using cryptographically secure random bytes."""
    # 16 bytes = 128 bits, which is sufficient for password salting
    return secrets.token_urlsafe(16)

if __name__ == '__main__':
    print("# Flask Application Secrets")
    print("# Generated using Python's secrets module (cryptographically secure)")
    print("# Copy these values to your .env file\n")
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"SECURITY_PASSWORD_SALT={generate_password_salt()}")
    print("\n# Remember to:")
    print("# 1. Copy these to your .env file")
    print("# 2. Never commit .env to version control")
    print("# 3. Use different secrets for each environment (dev/staging/prod)")
    print("# 4. Keep these secrets secure and rotate them periodically")


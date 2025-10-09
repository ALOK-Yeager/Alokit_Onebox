# Email Integration Security Guide
## Onebox Aggregator - Production-Ready IMAP Integration

---

## Table of Contents
1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Documentation](#api-documentation)
5. [Frontend Integration](#frontend-integration)
6. [Testing Guide](#testing-guide)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Overview

This guide covers the secure IMAP email integration feature for Onebox Aggregator. The implementation prioritizes security with encryption at rest, rate limiting, and proper authentication.

### Key Features
- ✅ **Secure Credential Storage**: Fernet encryption (AES-128) for passwords
- ✅ **OAuth2 Support**: For Gmail, Outlook, and other modern providers
- ✅ **Rate Limiting**: Protection against brute force attacks
- ✅ **Session Management**: Auto-expire credentials after 30 days
- ✅ **Incremental Sync**: Only fetch new emails
- ✅ **Multi-Provider**: Gmail, Outlook, Yahoo, iCloud, Custom IMAP
- ✅ **Production-Ready**: Docker support with proper secrets handling

---

## Security Architecture

### Encryption Flow

```
User enters password
      ↓
[Frontend] - HTTPS - [Backend API]
      ↓
SecureCredentials.encrypt()
      ↓
Fernet encryption (AES-128-CBC + HMAC)
      ↓
Store encrypted string in database
      ↓
[On use] Decrypt only when needed
      ↓
Clear from memory immediately after
```

### Key Security Features

1. **Encryption at Rest**
   - Uses Fernet (symmetric encryption)
   - 128-bit AES in CBC mode
   - HMAC authentication
   - Timestamped for expiration checking

2. **Rate Limiting**
   - 5 connection attempts per minute
   - 3 manual syncs per minute
   - Prevents brute force attacks

3. **Authentication**
   - JWT-based authentication required
   - User-scoped connections
   - Row-level security

4. **Session Management**
   - Credentials expire after 30 days
   - Automatic cleanup of expired credentials
   - Connection status tracking

---

## Setup Instructions

### Step 1: Generate Encryption Key

```bash
# Generate a secure encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output:
# vx8pDQZ3YqV8K7JmN9PFxW2HqG3LpKfR8tZ4VnX9YpQ=
```

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# CRITICAL: Encryption key for email credentials
CREDENTIALS_ENCRYPTION_KEY=<your_generated_key_here>

# Never commit this key to version control!
# Use different keys for dev/staging/production
```

### Step 3: Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# This includes:
# - cryptography==42.0.5 (Fernet encryption)
# - slowapi==0.1.9 (Rate limiting)
# - sqlalchemy==2.0.23 (Database ORM)
```

### Step 4: Setup Database

```python
# Run database migrations
from src.Services.email.models import Base
from your_database import engine

# Create tables
Base.metadata.create_all(engine)

# Tables created:
# - users
# - email_connections
# - email_sync_history
```

### Step 5: Integrate API Routes

In your main FastAPI application:

```python
from fastapi import FastAPI
from src.Services.email.email_routes import router as email_router

app = FastAPI()

# Mount email routes
app.include_router(email_router)

# Routes available at:
# POST /api/email/connect
# GET /api/email/connections
# GET /api/email/status/{connection_id}
# POST /api/email/disconnect/{connection_id}
# POST /api/email/sync/{connection_id}
# GET /api/email/providers
```

### Step 6: Frontend Integration

In your React application:

```tsx
import EmailConnectModal from './components/EmailConnectModal';
import ConnectionStatus from './components/ConnectionStatus';

function App() {
  const [showModal, setShowModal] = useState(false);
  
  const handleSuccess = (connection) => {
    console.log('Connected:', connection);
    // Reload connections list
  };
  
  return (
    <>
      <ConnectionStatus onConnectClick={() => setShowModal(true)} />
      
      <EmailConnectModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={handleSuccess}
      />
    </>
  );
}
```

---

## API Documentation

### POST /api/email/connect

Connect a new email account.

**Request:**
```json
{
  "email": "user@gmail.com",
  "password": "app-specific-password",
  "provider": "Gmail",
  "custom_imap_server": null,
  "custom_imap_port": 993
}
```

**Response (201):**
```json
{
  "id": "conn_123",
  "email_address": "user@gmail.com",
  "provider": "Gmail",
  "status": "connected",
  "last_sync_at": null,
  "sync_enabled": true,
  "created_at": "2025-10-08T15:30:00Z",
  "updated_at": "2025-10-08T15:30:00Z"
}
```

**Errors:**
- 401: Invalid credentials
- 400: Connection failed
- 429: Rate limit exceeded

**Rate Limit:** 5 attempts per minute

---

### GET /api/email/connections

List all connected email accounts for the authenticated user.

**Response (200):**
```json
[
  {
    "id": "conn_123",
    "email_address": "user@gmail.com",
    "provider": "Gmail",
    "status": "connected",
    "last_sync_at": "2025-10-08T15:35:00Z",
    "sync_enabled": true,
    "created_at": "2025-10-08T15:30:00Z",
    "updated_at": "2025-10-08T15:35:00Z"
  }
]
```

---

### GET /api/email/status/{connection_id}

Get detailed status of a specific connection.

**Response (200):**
```json
{
  "connection_id": "conn_123",
  "email": "user@gmail.com",
  "provider": "Gmail",
  "status": "connected",
  "is_connected": true,
  "last_sync_at": "2025-10-08T15:35:00Z",
  "last_error": null,
  "sync_history": [
    {
      "id": "sync_456",
      "started_at": "2025-10-08T15:35:00Z",
      "completed_at": "2025-10-08T15:36:00Z",
      "status": "success",
      "emails_fetched": 50,
      "emails_processed": 50,
      "emails_failed": 0
    }
  ]
}
```

---

### POST /api/email/disconnect/{connection_id}

Disconnect an email account (soft delete).

**Response (200):**
```json
{
  "connection_id": "conn_123",
  "status": "disconnected",
  "message": "Email account disconnected successfully"
}
```

---

### POST /api/email/sync/{connection_id}

Trigger manual email synchronization.

**Response (200):**
```json
{
  "status": "sync_started",
  "message": "Email synchronization started in background",
  "connection_id": "conn_123"
}
```

**Rate Limit:** 3 syncs per minute

---

### GET /api/email/providers

Get list of supported email providers (public endpoint).

**Response (200):**
```json
{
  "Gmail": {
    "name": "Gmail",
    "help_text": "Use App Password if 2FA is enabled...",
    "requires_oauth": true,
    "custom": false
  },
  "Outlook": {
    "name": "Outlook",
    "help_text": "Modern authentication required...",
    "requires_oauth": true,
    "custom": false
  }
}
```

---

## Frontend Integration

### EmailConnectModal Component

```tsx
import EmailConnectModal from './components/EmailConnectModal';

// Props interface
interface EmailConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (connection: EmailConnection) => void;
}

// Usage
<EmailConnectModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  onSuccess={(conn) => {
    console.log('Connected:', conn);
    // Refresh connections list
    loadConnections();
  }}
/>
```

**Features:**
- Provider auto-detection from email domain
- Real-time validation
- Security warnings
- Progress indication
- Error handling

---

### ConnectionStatus Component

```tsx
import ConnectionStatus from './components/ConnectionStatus';

// Props interface
interface ConnectionStatusProps {
  onConnectClick: () => void;
}

// Usage
<ConnectionStatus
  onConnectClick={() => setShowModal(true)}
/>
```

**Features:**
- List all connections
- Real-time status indicators
- Manual sync trigger
- Disconnect action
- Last sync timestamp

---

## Testing Guide

### Unit Tests

Test the encryption system:

```python
import pytest
from src.Services.email.email_service import SecureCredentials
import os

def test_encryption_decryption():
    # Set test encryption key
    os.environ['CREDENTIALS_ENCRYPTION_KEY'] = 'test_key_base64...'
    
    creds = SecureCredentials()
    password = "my_secure_password"
    
    # Encrypt
    encrypted = creds.encrypt(password)
    assert encrypted != password
    
    # Decrypt
    decrypted = creds.decrypt(encrypted)
    assert decrypted == password
    
    # Clear
    del creds
```

Test connection validation:

```python
from src.Services.email.email_service import ConnectionValidator

def test_connection_validation():
    # Test with invalid credentials
    success, message = ConnectionValidator.validate(
        email="test@gmail.com",
        password="wrong_password",
        provider="Gmail"
    )
    
    assert success == False
    assert "Invalid" in message
```

---

### Integration Tests

Test the full flow:

```bash
# 1. Generate test encryption key
export CREDENTIALS_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 2. Start services
docker-compose up -d

# 3. Test connection endpoint
curl -X POST http://localhost:3001/api/email/connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "email": "test@gmail.com",
    "password": "your_app_password",
    "provider": "Gmail"
  }'

# Expected response: 201 Created with connection details
```

---

### Testing with Gmail

1. **Enable 2FA** on your Google account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Generate and copy the 16-character password
3. **Use in Onebox**:
   - Provider: Gmail
   - Email: your.email@gmail.com
   - Password: Use the 16-character app password

---

### Testing with Outlook

1. **Enable Modern Authentication**
2. **Create App Password**:
   - Go to https://account.microsoft.com/security
   - Select "Advanced security options"
   - Create new app password
3. **Use in Onebox**:
   - Provider: Outlook
   - Email: your.email@outlook.com
   - Password: Use the generated app password

---

## Troubleshooting

### Common Issues

#### 1. "CREDENTIALS_ENCRYPTION_KEY not set"

**Problem:** Missing encryption key in environment.

**Solution:**
```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "CREDENTIALS_ENCRYPTION_KEY=<your_key>" >> .env

# Restart services
docker-compose restart
```

---

#### 2. "Invalid email or password"

**Problem:** Authentication failing with email provider.

**Solution:**
- **Gmail**: Use App Password, not regular password
- **Outlook**: Enable modern authentication
- **Yahoo**: Generate App Password from security settings
- Check 2FA is properly configured

---

#### 3. "Too many connection attempts"

**Problem:** Rate limit reached.

**Solution:**
- Wait 1 minute before retrying
- Check for automation scripts hitting the endpoint
- Increase rate limit in production if needed

---

#### 4. "Connection timeout"

**Problem:** IMAP server not responding.

**Solution:**
- Check internet connectivity
- Verify IMAP server address and port
- Check firewall settings
- Try custom IMAP settings if provider-specific fails

---

#### 5. "Credentials have expired"

**Problem:** Stored credentials older than 30 days.

**Solution:**
- Reconnect the email account
- Credentials auto-expire for security
- Update max age in `SecureCredentials.decrypt()` if needed

---

## Production Deployment

### Docker Secrets (Recommended)

```bash
# 1. Create encryption key secret
echo "your_encryption_key" | docker secret create credentials_encryption_key -

# 2. Update docker-compose.yml
services:
  api-server:
    secrets:
      - credentials_encryption_key
    environment:
      - CREDENTIALS_ENCRYPTION_KEY_FILE=/run/secrets/credentials_encryption_key

secrets:
  credentials_encryption_key:
    external: true
```

---

### Environment Variables

For cloud platforms (AWS, GCP, Azure):

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name onebox/credentials-encryption-key \
  --secret-string "your_encryption_key"

# Load in application startup
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='onebox/credentials-encryption-key')
os.environ['CREDENTIALS_ENCRYPTION_KEY'] = response['SecretString']
```

---

### Key Rotation

Rotate encryption keys every 90 days:

```python
# Script: rotate_encryption_key.py
from src.Services.email.email_service import SecureCredentials
from src.Services.email.models import EmailConnection
from your_database import SessionLocal

def rotate_keys(old_key, new_key):
    db = SessionLocal()
    
    # Initialize both encryptors
    old_creds = SecureCredentials()
    old_creds.key = old_key.encode()
    old_creds.fernet = Fernet(old_creds.key)
    
    new_creds = SecureCredentials()
    new_creds.key = new_key.encode()
    new_creds.fernet = Fernet(new_creds.key)
    
    # Re-encrypt all credentials
    connections = db.query(EmailConnection).filter(
        EmailConnection.is_deleted == False
    ).all()
    
    for conn in connections:
        try:
            # Decrypt with old key
            password = old_creds.decrypt(conn.encrypted_password)
            
            # Encrypt with new key
            conn.encrypted_password = new_creds.encrypt(password)
            
            db.commit()
            print(f"Rotated key for {conn.email_address}")
        except Exception as e:
            print(f"Failed to rotate {conn.email_address}: {e}")
            db.rollback()
    
    db.close()

# Usage
rotate_keys(
    old_key="old_encryption_key",
    new_key="new_encryption_key"
)
```

---

### Security Checklist

Before going to production:

- [ ] Generated unique encryption key for production
- [ ] Stored encryption key in secure secrets manager
- [ ] Enabled rate limiting on all endpoints
- [ ] Configured JWT authentication properly
- [ ] Set up HTTPS/TLS for all API endpoints
- [ ] Enabled database encryption at rest
- [ ] Configured proper CORS policies
- [ ] Set up monitoring and alerting
- [ ] Implemented audit logging
- [ ] Tested key rotation procedure
- [ ] Documented incident response plan
- [ ] Configured automatic credential expiration
- [ ] Set up regular security audits

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/ALOK-Yeager/Alokit_Onebox/issues
- Documentation: See `docs/` directory
- Security Issues: Email security@onebox.com

---

**Last Updated:** October 8, 2025
**Version:** 1.0.0

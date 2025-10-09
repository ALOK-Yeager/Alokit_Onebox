"""
Email Integration - Quick Start Example
========================================

This example shows how to quickly integrate the email connection feature
into your existing Onebox Aggregator application.

Author: Onebox Team
Version: 1.0.0
"""

# ============================================================================
# STEP 1: Backend Integration (FastAPI)
# ============================================================================

from fastapi import FastAPI
from src.Services.email.email_routes import router as email_router

app = FastAPI(title="Onebox Aggregator")

# Mount email routes
app.include_router(email_router)

# Routes now available:
# POST /api/email/connect
# GET /api/email/connections
# GET /api/email/status/{connection_id}
# POST /api/email/disconnect/{connection_id}
# POST /api/email/sync/{connection_id}
# GET /api/email/providers


# ============================================================================
# STEP 2: Database Setup
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.Services.email.models import Base, User, EmailConnection, EmailSyncHistory

# Create engine
DATABASE_URL = "postgresql://user:password@localhost/onebox"  # or sqlite:///./onebox.db
engine = create_engine(DATABASE_URL)

# Create tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# STEP 3: Environment Configuration
# ============================================================================

import os
from cryptography.fernet import Fernet

# Generate encryption key (do this once, save securely)
def generate_encryption_key():
    """Generate a new encryption key for credentials"""
    key = Fernet.generate_key()
    print(f"CREDENTIALS_ENCRYPTION_KEY={key.decode()}")
    return key

# Set in environment
# os.environ['CREDENTIALS_ENCRYPTION_KEY'] = 'your_generated_key_here'


# ============================================================================
# STEP 4: Example Usage - Connect Email
# ============================================================================

from src.Services.email.email_service import (
    SecureCredentials,
    EmailFetcher,
    ConnectionValidator
)

def example_connect_email():
    """Example: Validate and connect an email account"""
    
    # User inputs
    email = "user@gmail.com"
    password = "app_specific_password"
    provider = "Gmail"
    
    # Step 1: Validate credentials
    is_valid, message = ConnectionValidator.validate(
        email=email,
        password=password,
        provider=provider
    )
    
    if not is_valid:
        print(f"Validation failed: {message}")
        return
    
    # Step 2: Encrypt password
    secure_creds = SecureCredentials()
    encrypted_password = secure_creds.encrypt(password)
    
    # Step 3: Save to database
    db = SessionLocal()
    connection = EmailConnection(
        user_id="user_123",  # Get from your auth system
        email_address=email,
        provider=provider,
        encrypted_password=encrypted_password,
        status='connected'
    )
    db.add(connection)
    db.commit()
    
    print(f"✓ Connected {email}")
    
    # Step 4: Fetch emails
    fetcher = EmailFetcher(
        email=email,
        encrypted_password=encrypted_password,
        provider=provider
    )
    
    emails = fetcher.fetch_batch(batch_size=10)
    print(f"✓ Fetched {len(emails)} emails")
    
    db.close()


# ============================================================================
# STEP 5: Example Usage - List Connections
# ============================================================================

def example_list_connections(user_id: str):
    """Example: List all email connections for a user"""
    
    db = SessionLocal()
    connections = db.query(EmailConnection).filter(
        EmailConnection.user_id == user_id,
        EmailConnection.is_deleted == False
    ).all()
    
    for conn in connections:
        print(f"{conn.provider}: {conn.email_address} - {conn.status}")
    
    db.close()


# ============================================================================
# STEP 6: Example Usage - Sync Emails
# ============================================================================

from datetime import datetime, timedelta

async def example_sync_emails(connection_id: str):
    """Example: Sync emails for a connection"""
    
    db = SessionLocal()
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == connection_id
    ).first()
    
    if not connection:
        print("Connection not found")
        return
    
    # Create fetcher
    fetcher = EmailFetcher(
        email=connection.email_address,
        encrypted_password=connection.encrypted_password,
        provider=connection.provider,
        custom_server=connection.custom_imap_server,
        custom_port=connection.custom_imap_port
    )
    
    # Fetch emails from last 7 days
    since_date = datetime.utcnow() - timedelta(days=7)
    emails = fetcher.fetch_batch(since_date=since_date, batch_size=50)
    
    # Process emails (index in Elasticsearch, VectorDB, etc.)
    for email_msg in emails:
        print(f"Processing: {email_msg.subject}")
        # TODO: Index in your search engine
        # TODO: Add to vector database
        # TODO: Apply AI classification
    
    # Update sync history
    sync_record = EmailSyncHistory(
        connection_id=connection_id,
        status='success',
        emails_fetched=len(emails),
        emails_processed=len(emails),
        completed_at=datetime.utcnow()
    )
    db.add(sync_record)
    
    # Update connection
    connection.last_sync_at = datetime.utcnow()
    db.commit()
    
    print(f"✓ Synced {len(emails)} emails")
    db.close()


# ============================================================================
# STEP 7: Example Usage - Disconnect Email
# ============================================================================

def example_disconnect_email(connection_id: str, user_id: str):
    """Example: Disconnect an email account"""
    
    db = SessionLocal()
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == connection_id,
        EmailConnection.user_id == user_id,
        EmailConnection.is_deleted == False
    ).first()
    
    if not connection:
        print("Connection not found or already disconnected")
        return
    
    # Soft delete
    connection.is_deleted = True
    connection.deleted_at = datetime.utcnow()
    connection.status = 'disconnected'
    connection.sync_enabled = False
    
    db.commit()
    print(f"✓ Disconnected {connection.email_address}")
    db.close()


# ============================================================================
# STEP 8: Frontend Integration Example
# ============================================================================

"""
In your React component:

import React, { useState } from 'react';
import EmailConnectModal from './components/EmailConnectModal';
import ConnectionStatus from './components/ConnectionStatus';

function EmailSettings() {
  const [showModal, setShowModal] = useState(false);

  const handleSuccess = (connection) => {
    console.log('Successfully connected:', connection);
    // Refresh connections list or show success message
  };

  return (
    <div className="email-settings">
      <h1>Email Settings</h1>
      
      {/* Connection Status Component */}
      <ConnectionStatus 
        onConnectClick={() => setShowModal(true)}
      />
      
      {/* Connection Modal */}
      <EmailConnectModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
}

export default EmailSettings;
"""


# ============================================================================
# STEP 9: Automated Background Sync (Optional)
# ============================================================================

import asyncio
from datetime import datetime

async def background_sync_scheduler():
    """Run background sync for all active connections"""
    
    while True:
        try:
            db = SessionLocal()
            
            # Get all active connections
            connections = db.query(EmailConnection).filter(
                EmailConnection.status == 'connected',
                EmailConnection.sync_enabled == True,
                EmailConnection.is_deleted == False
            ).all()
            
            for connection in connections:
                # Check if sync is due
                if connection.last_sync_at:
                    time_since_sync = (datetime.utcnow() - connection.last_sync_at).seconds / 60
                    if time_since_sync < connection.sync_frequency_minutes:
                        continue
                
                # Sync this connection
                await example_sync_emails(connection.id)
            
            db.close()
            
        except Exception as e:
            print(f"Background sync error: {e}")
        
        # Wait 5 minutes before next check
        await asyncio.sleep(300)


# ============================================================================
# STEP 10: Run the Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Onebox Aggregator - Email Integration Example")
    print("=" * 60)
    
    # Check encryption key
    if not os.getenv('CREDENTIALS_ENCRYPTION_KEY'):
        print("\n⚠️  WARNING: CREDENTIALS_ENCRYPTION_KEY not set!")
        print("Generate one with:")
        print("  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        print()
        
        # Generate for development (NOT for production!)
        if input("Generate key for development? (y/n): ").lower() == 'y':
            key = generate_encryption_key()
            os.environ['CREDENTIALS_ENCRYPTION_KEY'] = key.decode()
    
    print("\n✓ Starting Onebox Aggregator API Server")
    print("✓ Email integration routes mounted at /api/email/*")
    print()
    print("Available endpoints:")
    print("  POST   /api/email/connect")
    print("  GET    /api/email/connections")
    print("  GET    /api/email/status/{connection_id}")
    print("  POST   /api/email/disconnect/{connection_id}")
    print("  POST   /api/email/sync/{connection_id}")
    print("  GET    /api/email/providers")
    print()
    
    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

"""
Test with curl:

# 1. Get list of providers
curl http://localhost:8000/api/email/providers

# 2. Connect email (requires auth token)
curl -X POST http://localhost:8000/api/email/connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "email": "test@gmail.com",
    "password": "your_app_password",
    "provider": "Gmail"
  }'

# 3. List connections
curl http://localhost:8000/api/email/connections \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Trigger sync
curl -X POST http://localhost:8000/api/email/sync/CONNECTION_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 5. Disconnect
curl -X POST http://localhost:8000/api/email/disconnect/CONNECTION_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
"""


# ============================================================================
# SECURITY REMINDERS
# ============================================================================

"""
CRITICAL SECURITY CHECKLIST:
✓ Never commit CREDENTIALS_ENCRYPTION_KEY to git
✓ Use different keys for dev/staging/production
✓ Rotate encryption keys every 90 days
✓ Enable HTTPS/TLS in production
✓ Implement proper JWT authentication
✓ Set up rate limiting
✓ Monitor for suspicious activity
✓ Regular security audits
✓ Implement audit logging
✓ Use Docker secrets in production
"""

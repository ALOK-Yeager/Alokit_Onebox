"""
Database Models for Email Connection Management
===============================================

Defines SQLAlchemy models for storing user email connections
with encrypted credentials.

Security Features:
- Encrypted password storage
- User association for multi-tenancy
- Connection status tracking
- Audit logging (created_at, updated_at)
- Soft delete support

Author: Onebox Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class EmailConnection(Base):
    """
    Stores encrypted email connection credentials.
    
    Security Notes:
    - password field contains Fernet-encrypted credentials
    - Never query this table without proper authentication
    - Implement row-level security in production
    - Audit all access to this table
    """
    
    __tablename__ = 'email_connections'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User association (foreign key to users table)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
    # Email connection details
    email_address = Column(String(255), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # Gmail, Outlook, Yahoo, etc.
    
    # Encrypted credentials (NEVER store plaintext)
    encrypted_password = Column(Text, nullable=False)
    
    # Custom IMAP settings (for "Custom IMAP" provider)
    custom_imap_server = Column(String(255), nullable=True)
    custom_imap_port = Column(Integer, nullable=True, default=993)
    
    # Connection status
    status = Column(String(20), nullable=False, default='pending')  # pending, connected, disconnected, error
    last_sync_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Sync settings
    sync_enabled = Column(Boolean, default=True)
    sync_frequency_minutes = Column(Integer, default=15)
    last_fetched_uid = Column(String(100), nullable=True)  # Track incremental sync
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="email_connections")
    sync_history = relationship("EmailSyncHistory", back_populates="connection", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email', 'user_id', 'email_address'),
        Index('idx_status', 'status'),
        Index('idx_sync_enabled', 'sync_enabled'),
        Index('idx_deleted', 'is_deleted'),
    )
    
    def __repr__(self):
        return f"<EmailConnection(id={self.id}, email={self.email_address}, provider={self.provider}, status={self.status})>"
    
    def to_dict(self, include_sensitive=False):
        """
        Convert to dictionary for API responses.
        
        Args:
            include_sensitive: Whether to include encrypted password (default: False)
        
        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'email_address': self.email_address,
            'provider': self.provider,
            'status': self.status,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_enabled': self.sync_enabled,
            'sync_frequency_minutes': self.sync_frequency_minutes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Only include encrypted password if explicitly requested (for internal use)
        if include_sensitive:
            data['encrypted_password'] = self.encrypted_password
            data['custom_imap_server'] = self.custom_imap_server
            data['custom_imap_port'] = self.custom_imap_port
        
        return data


class EmailSyncHistory(Base):
    """
    Tracks email synchronization history for audit and debugging.
    
    Useful for:
    - Troubleshooting sync issues
    - Rate limit tracking
    - Performance monitoring
    - Audit trails
    """
    
    __tablename__ = 'email_sync_history'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to connection
    connection_id = Column(String(36), ForeignKey('email_connections.id'), nullable=False, index=True)
    
    # Sync details
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # success, failed, partial
    
    # Statistics
    emails_fetched = Column(Integer, default=0)
    emails_processed = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Relationship
    connection = relationship("EmailConnection", back_populates="sync_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_connection_started', 'connection_id', 'started_at'),
        Index('idx_status_sync', 'status'),
    )
    
    def __repr__(self):
        return f"<EmailSyncHistory(id={self.id}, connection_id={self.connection_id}, status={self.status}, emails={self.emails_fetched})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'connection_id': self.connection_id,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'emails_fetched': self.emails_fetched,
            'emails_processed': self.emails_processed,
            'emails_failed': self.emails_failed,
            'error_message': self.error_message
        }


class User(Base):
    """
    User model (simplified - extend based on your auth system)
    
    Note: This is a basic implementation. In production, integrate with
    your existing authentication system (Auth0, Firebase, custom JWT, etc.)
    """
    
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    
    # Password hash (for the Onebox account, not email accounts)
    password_hash = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    email_connections = relationship("EmailConnection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses (excludes password_hash)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }


# Export models
__all__ = ['EmailConnection', 'EmailSyncHistory', 'User', 'Base']

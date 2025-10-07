"""Production-ready Discord notification service for email alerts.

This module provides a robust Discord bot integration for sending formatted email notifications
to specified Discord channels. It handles connection management, rate limiting, error recovery,
and provides rich formatting for email metadata.

Setup Instructions
------------------
1. Create a Discord Bot:
   - Go to https://discord.com/developers/applications
   - Click "New Application" and give it a name (e.g., "Email Notifier")
   - Go to "Bot" section and click "Add Bot"
   - Under "Privileged Gateway Intents", enable "Message Content Intent" if needed
   - Copy the bot token (you'll need this for .env)

2. Invite Bot to Your Server:
   - Go to "OAuth2" > "URL Generator"
   - Select scopes: "bot"
   - Select permissions: "Send Messages", "Embed Links", "Read Message History"
   - Copy the generated URL and open it in a browser
   - Select your server and authorize

3. Get Channel ID:
   - In Discord, enable Developer Mode (Settings > Advanced > Developer Mode)
   - Right-click the channel where you want notifications
   - Click "Copy ID"

4. Configure Environment Variables:
   Add to your .env file:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   DISCORD_CHANNEL_ID=1234567890123456789
   DISCORD_APP_URL=https://yourapp.com/emails  # Optional: link to email view
   ```

5. Install Dependencies:
   ```bash
   pip install discord.py python-dotenv
   ```

6. Usage:
   ```python
   from src.Services.notifications.DiscordNotifier import DiscordNotifier

   notifier = DiscordNotifier()
   await notifier.start()  # Start the bot connection

   await notifier.send_email_notification(
       from_address="client@example.com",
       subject="Important Project Update",
       category="Work",
       email_id="msg-12345",
       confidence=0.92
   )

   await notifier.stop()  # Clean shutdown
   ```

Features
--------
- Async/await for non-blocking operations
- Automatic reconnection on connection loss
- Rate limit handling with exponential backoff
- Rich embed formatting with color coding by category
- Comprehensive error logging and recovery
- Graceful shutdown and resource cleanup
- Thread-safe operation

Architecture
------------
Uses discord.py Client with manual event loop management for integration into
existing async applications. Handles Discord API rate limits (50 requests per second
per bot, with per-channel limits) transparently.

Limitations
-----------
- Discord embed character limits: Title (256), Description (4096), Field (1024)
- Rate limits: 50 requests/sec globally, 5 requests/5sec per channel
- Message size: 2000 characters (handled by truncation)

Author: Onebox Aggregator Team
License: Same as parent project
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

import discord
from discord import Embed, Color
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ======================== Configuration ======================== #

@dataclass
class DiscordConfig:
    """Configuration for Discord notification service."""
    bot_token: Optional[str] = None
    channel_id: Optional[int] = None
    app_url: Optional[str] = None
    enabled: bool = False
    reconnect_attempts: int = 5
    reconnect_delay: float = 2.0
    rate_limit_retry: bool = True

    @classmethod
    def from_env(cls) -> DiscordConfig:
        """Load configuration from environment variables."""
        bot_token = os.getenv("DISCORD_BOT_TOKEN")
        channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
        app_url = os.getenv("DISCORD_APP_URL", "https://app.example.com/emails")
        
        channel_id = None
        if channel_id_str:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                logger.error(f"Invalid DISCORD_CHANNEL_ID: {channel_id_str}")
        
        enabled = bool(bot_token and channel_id)
        
        return cls(
            bot_token=bot_token,
            channel_id=channel_id,
            app_url=app_url,
            enabled=enabled
        )

# ======================== Discord Client ======================== #

class DiscordNotifier:
    """Production-ready Discord notification service for email alerts.
    
    This class manages a Discord bot connection and sends formatted notifications
    about incoming emails to a specified channel. It handles all edge cases including
    rate limits, connection failures, and provides rich message formatting.
    
    Thread Safety: This class uses asyncio and is safe for concurrent async operations.
    The discord.py library handles internal synchronization.
    
    Attributes:
        config: Configuration loaded from environment variables
        client: Discord client instance (None until started)
        channel: Target Discord channel object (None until connected)
        ready: Event indicating bot is ready
        enabled: Whether the service is enabled and operational
    """

    # Category to Discord embed color mapping
    CATEGORY_COLORS: Dict[str, Color] = {
        "Work": Color.blue(),
        "Personal": Color.green(),
        "Promotional": Color.orange(),
        "Social": Color.purple(),
        "Notifications": Color.lighter_grey(),
        "Finance": Color.gold(),
        "Shopping": Color.magenta(),
        "Travel": Color.teal(),
        "Support": Color.red(),
        "Security": Color.dark_red(),
        "Uncertain": Color.light_grey(),
        "Unclassified": Color.dark_grey(),
    }

    def __init__(self, config: Optional[DiscordConfig] = None):
        """Initialize Discord notifier.
        
        Args:
            config: Optional configuration. If None, loads from environment.
        """
        self.config = config or DiscordConfig.from_env()
        self.client: Optional[discord.Client] = None
        self.channel: Optional[discord.TextChannel] = None
        self.ready = asyncio.Event()
        self.enabled = self.config.enabled
        self._reconnect_attempts = 0
        self._rate_limit_hits = 0
        
        if not self.enabled:
            if not self.config.bot_token:
                logger.info("ℹ️ Discord notifications disabled (no DISCORD_BOT_TOKEN)")
            elif not self.config.channel_id:
                logger.info("ℹ️ Discord notifications disabled (no DISCORD_CHANNEL_ID)")
        else:
            logger.info("✅ Discord notifications enabled")

    async def start(self) -> bool:
        """Start the Discord bot connection.
        
        This method initializes the Discord client and establishes a connection.
        It must be called before sending notifications.
        
        Returns:
            bool: True if successfully started, False otherwise.
            
        Raises:
            ValueError: If configuration is invalid
            discord.LoginFailure: If bot token is invalid
        """
        if not self.enabled:
            logger.warning("Cannot start: Discord notifications not enabled")
            return False
        
        if self.client and not self.client.is_closed():
            logger.warning("Discord client already running")
            return True
        
        try:
            # Initialize Discord client with minimal intents
            intents = discord.Intents.default()
            intents.message_content = False  # We only send, don't need to read
            
            self.client = discord.Client(intents=intents)
            
            # Register event handlers
            @self.client.event
            async def on_ready():
                """Called when bot successfully connects."""
                logger.info(f"Discord bot connected as {self.client.user}")
                try:
                    self.channel = await self.client.fetch_channel(self.config.channel_id)
                    logger.info(f"Target channel: #{self.channel.name}")
                    self._reconnect_attempts = 0  # Reset on successful connection
                    self.ready.set()
                except discord.NotFound:
                    logger.error(f"Channel ID {self.config.channel_id} not found")
                    self.enabled = False
                except discord.Forbidden:
                    logger.error(f"Bot lacks permissions for channel {self.config.channel_id}")
                    self.enabled = False
                except Exception as e:
                    logger.error(f"Failed to fetch channel: {e}", exc_info=True)
                    self.enabled = False
            
            @self.client.event
            async def on_disconnect():
                """Called when bot disconnects."""
                logger.warning("Discord bot disconnected")
                self.ready.clear()
            
            @self.client.event
            async def on_resumed():
                """Called when connection is resumed."""
                logger.info("Discord bot connection resumed")
                self.ready.set()
            
            @self.client.event
            async def on_error(event, *args, **kwargs):
                """Global error handler."""
                logger.error(f"Discord error in {event}", exc_info=True)
            
            # Start bot in background task
            asyncio.create_task(self._run_bot())
            
            # Wait for ready with timeout
            try:
                await asyncio.wait_for(self.ready.wait(), timeout=10.0)
                logger.info("Discord bot ready to send notifications")
                return True
            except asyncio.TimeoutError:
                logger.error("Discord bot failed to become ready within 10 seconds")
                await self.stop()
                return False
                
        except discord.LoginFailure as e:
            logger.error(f"Invalid Discord bot token: {e}")
            self.enabled = False
            return False
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}", exc_info=True)
            self.enabled = False
            return False

    async def _run_bot(self):
        """Internal method to run the bot with reconnection logic."""
        while self._reconnect_attempts < self.config.reconnect_attempts:
            try:
                await self.client.start(self.config.bot_token)
            except discord.LoginFailure:
                logger.error("Login failed - invalid token")
                break
            except Exception as e:
                self._reconnect_attempts += 1
                if self._reconnect_attempts < self.config.reconnect_attempts:
                    delay = self.config.reconnect_delay * (2 ** (self._reconnect_attempts - 1))
                    logger.warning(
                        f"Connection lost, retrying in {delay}s "
                        f"(attempt {self._reconnect_attempts}/{self.config.reconnect_attempts})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max reconnection attempts reached: {e}")
                    self.enabled = False
                    break

    async def stop(self):
        """Gracefully shutdown the Discord bot.
        
        This method closes the connection and cleans up resources.
        Always call this before application shutdown.
        """
        if self.client and not self.client.is_closed():
            logger.info("Shutting down Discord bot...")
            await self.client.close()
            self.ready.clear()
            logger.info("Discord bot stopped")

    def _truncate(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Safely truncate text to max length."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    def _get_category_color(self, category: str) -> Color:
        """Get Discord color for a category."""
        return self.CATEGORY_COLORS.get(category, Color.default())

    async def send_email_notification(
        self,
        from_address: str,
        subject: str,
        category: str,
        email_id: str,
        confidence: Optional[float] = None,
        preview: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a formatted email notification to Discord.
        
        This is the main method for sending notifications. It creates a rich embed
        with email details and sends it to the configured channel.
        
        Args:
            from_address: Email sender address
            subject: Email subject line
            category: Classification category (Work, Personal, etc.)
            email_id: Unique email identifier
            confidence: Optional classification confidence score (0.0-1.0)
            preview: Optional email body preview (first ~200 chars)
            timestamp: Optional email timestamp (defaults to now)
            metadata: Optional additional metadata to include
            
        Returns:
            bool: True if notification sent successfully, False otherwise.
            
        Example:
            >>> notifier = DiscordNotifier()
            >>> await notifier.start()
            >>> await notifier.send_email_notification(
            ...     from_address="client@example.com",
            ...     subject="Project Update",
            ...     category="Work",
            ...     email_id="msg-123",
            ...     confidence=0.95
            ... )
            True
        """
        if not self.enabled:
            logger.debug("Discord notifications disabled, skipping")
            return False
        
        if not self.ready.is_set():
            logger.warning("Discord bot not ready, cannot send notification")
            return False
        
        try:
            # Build rich embed
            embed = Embed(
                title=self._truncate(subject, 256),
                color=self._get_category_color(category),
                timestamp=timestamp or datetime.utcnow()
            )
            
            # Add fields
            embed.add_field(name="📧 From", value=self._truncate(from_address, 1024), inline=True)
            embed.add_field(name="🏷️ Category", value=category, inline=True)
            
            if confidence is not None:
                confidence_str = f"{confidence:.1%}"
                embed.add_field(name="📊 Confidence", value=confidence_str, inline=True)
            
            # Add preview if provided
            if preview:
                preview_text = self._truncate(preview, 300)
                embed.add_field(name="📄 Preview", value=preview_text, inline=False)
            
            # Add metadata if provided
            if metadata:
                meta_str = "\n".join(f"• {k}: {v}" for k, v in list(metadata.items())[:5])
                if meta_str:
                    embed.add_field(name="ℹ️ Details", value=self._truncate(meta_str, 1024), inline=False)
            
            # Add link to app if configured
            if self.config.app_url:
                email_url = f"{self.config.app_url}/{email_id}"
                embed.add_field(name="🔗 View Email", value=f"[Open in App]({email_url})", inline=False)
            
            # Set footer
            embed.set_footer(text=f"Email ID: {email_id}")
            
            # Send with retry on rate limit
            max_retries = 3
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    await self.channel.send(embed=embed)
                    logger.debug(f"Discord notification sent for email {email_id}")
                    return True
                    
                except discord.HTTPException as e:
                    if e.status == 429:  # Rate limited
                        self._rate_limit_hits += 1
                        if attempt < max_retries - 1:
                            retry_after = getattr(e, 'retry_after', retry_delay)
                            logger.warning(
                                f"Discord rate limit hit (#{self._rate_limit_hits}), "
                                f"retrying in {retry_after}s"
                            )
                            await asyncio.sleep(retry_after)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error("Max retries exceeded for rate limit")
                            return False
                    else:
                        logger.error(f"Discord HTTP error {e.status}: {e.text}")
                        return False
                        
                except discord.Forbidden:
                    logger.error("Bot lacks permissions to send messages in channel")
                    self.enabled = False
                    return False
                    
                except discord.NotFound:
                    logger.error("Channel no longer exists")
                    self.enabled = False
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}", exc_info=True)
            return False
        
        return False  # Should not reach here

    def is_enabled(self) -> bool:
        """Check if Discord notifications are enabled and operational."""
        return self.enabled and self.ready.is_set()

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "enabled": self.enabled,
            "connected": self.client and not self.client.is_closed() if self.client else False,
            "ready": self.ready.is_set(),
            "rate_limit_hits": self._rate_limit_hits,
            "reconnect_attempts": self._reconnect_attempts,
            "channel_id": self.config.channel_id,
            "channel_name": self.channel.name if self.channel else None,
        }

# ======================== Context Manager Support ======================== #

class DiscordNotifierContext:
    """Context manager for Discord notifier lifecycle."""
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        self.notifier = DiscordNotifier(config)
    
    async def __aenter__(self) -> DiscordNotifier:
        await self.notifier.start()
        return self.notifier
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.notifier.stop()
        return False

# ======================== Convenience Function ======================== #

async def send_notification(
    from_address: str,
    subject: str,
    category: str,
    email_id: str,
    **kwargs
) -> bool:
    """Convenience function for one-shot notifications.
    
    Creates a notifier, sends the notification, and cleans up.
    For multiple notifications, use DiscordNotifier directly for better performance.
    
    Args:
        from_address: Email sender
        subject: Email subject
        category: Classification category
        email_id: Email ID
        **kwargs: Additional arguments passed to send_email_notification
        
    Returns:
        bool: Success status
    """
    async with DiscordNotifierContext() as notifier:
        return await notifier.send_email_notification(
            from_address=from_address,
            subject=subject,
            category=category,
            email_id=email_id,
            **kwargs
        )

__all__ = [
    "DiscordNotifier",
    "DiscordConfig",
    "DiscordNotifierContext",
    "send_notification"
]

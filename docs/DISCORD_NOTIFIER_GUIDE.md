# Discord Notifier Setup Guide

## Overview

The DiscordNotifier service provides production-ready Discord bot integration for sending real-time email notifications to your Discord server. It features robust error handling, rate limit management, rich formatting, and async operations for seamless integration.

## Features

✅ **Async/Await**: Non-blocking operations for high-throughput pipelines  
✅ **Auto-Reconnection**: Handles connection drops with exponential backoff  
✅ **Rate Limit Handling**: Automatic retry with Discord API rate limits  
✅ **Rich Embeds**: Color-coded categories, formatted metadata, preview text  
✅ **Error Recovery**: Comprehensive exception handling and logging  
✅ **Resource Management**: Graceful shutdown with context manager support  
✅ **Thread-Safe**: Safe for concurrent async operations  

## Quick Start

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it (e.g., "Email Notifier")
3. Navigate to **"Bot"** section → Click **"Add Bot"**
4. Under **"Privileged Gateway Intents"**, enable:
   - ✅ Message Content Intent (if reading messages)
5. Click **"Reset Token"** → Copy the bot token (save securely)

### 2. Invite Bot to Server

1. Go to **"OAuth2"** → **"URL Generator"**
2. Select **Scopes**: `bot`
3. Select **Bot Permissions**:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
4. Copy generated URL → Open in browser → Select server → Authorize

### 3. Get Channel ID

1. In Discord, enable **Developer Mode**:
   - Settings → Advanced → Developer Mode (toggle ON)
2. Right-click the channel where you want notifications
3. Click **"Copy ID"**

### 4. Configure Environment

Create/update `.env` file:

```env
# Required
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=1234567890123456789

# Optional
DISCORD_APP_URL=https://yourapp.com/emails
```

### 5. Install Dependencies

```bash
pip install discord.py python-dotenv
```

Or from requirements:

```bash
pip install -r python-requirements.txt
```

### 6. Basic Usage

```python
import asyncio
from src.Services.notifications.DiscordNotifier import DiscordNotifier

async def main():
    notifier = DiscordNotifier()
    await notifier.start()
    
    await notifier.send_email_notification(
        from_address="client@example.com",
        subject="Important Project Update",
        category="Work",
        email_id="msg-12345",
        confidence=0.92,
        preview="Hi team, just wanted to share..."
    )
    
    await notifier.stop()

asyncio.run(main())
```

## API Reference

### DiscordNotifier Class

#### Constructor

```python
DiscordNotifier(config: Optional[DiscordConfig] = None)
```

Loads configuration from environment if not provided.

#### Methods

**`async start() -> bool`**
- Establishes Discord connection
- Must be called before sending notifications
- Returns `True` on success

**`async stop()`**
- Gracefully shuts down connection
- Always call before application exit

**`async send_email_notification(...) -> bool`**
- Sends formatted email notification
- Parameters:
  - `from_address` (str): Sender email
  - `subject` (str): Email subject
  - `category` (str): Classification category
  - `email_id` (str): Unique identifier
  - `confidence` (Optional[float]): 0.0-1.0 score
  - `preview` (Optional[str]): Email body preview
  - `timestamp` (Optional[datetime]): Email timestamp
  - `metadata` (Optional[Dict]): Additional info
- Returns `True` on success

**`is_enabled() -> bool`**
- Check if service is operational

**`get_stats() -> Dict`**
- Get service statistics

### Context Manager

```python
from src.Services.notifications.DiscordNotifier import DiscordNotifierContext

async with DiscordNotifierContext() as notifier:
    await notifier.send_email_notification(...)
# Automatically stops on exit
```

### Convenience Function

```python
from src.Services.notifications.DiscordNotifier import send_notification

# One-shot notification (creates/destroys notifier)
success = await send_notification(
    from_address="test@example.com",
    subject="Test",
    category="Work",
    email_id="msg-1"
)
```

## Message Formatting

### Color Coding by Category

| Category | Color |
|----------|-------|
| Work | Blue |
| Personal | Green |
| Promotional | Orange |
| Social | Purple |
| Notifications | Light Grey |
| Finance | Gold |
| Shopping | Magenta |
| Travel | Teal |
| Support | Red |
| Security | Dark Red |
| Uncertain | Light Grey |
| Unclassified | Dark Grey |

### Embed Structure

```
┌─────────────────────────────────────┐
│ 📧 Email Subject (Color-coded)      │
├─────────────────────────────────────┤
│ 📧 From: sender@example.com         │
│ 🏷️ Category: Work                   │
│ 📊 Confidence: 92.0%                │
│                                     │
│ 📄 Preview                          │
│ Email content preview...            │
│                                     │
│ ℹ️ Details                          │
│ • key: value                        │
│ • key2: value2                      │
│                                     │
│ 🔗 View Email                       │
│ [Open in App](link)                 │
├─────────────────────────────────────┤
│ Email ID: msg-12345                 │
│ Timestamp: 2025-10-07 10:30 UTC     │
└─────────────────────────────────────┘
```

## Error Handling

### Connection Errors

```python
notifier = DiscordNotifier()
started = await notifier.start()

if not started:
    print("Failed to start - check logs")
    # Logs will show:
    # - Invalid token
    # - Network issues
    # - Channel not found
    # - Permission issues
```

### Rate Limits

The service automatically handles rate limits:

- **Global**: 50 requests/second per bot
- **Per-Channel**: 5 requests/5 seconds
- **Behavior**: Exponential backoff retry (up to 3 attempts)

```python
# Rate limit handling is automatic
for i in range(100):
    await notifier.send_email_notification(...)
    # Automatically waits if rate limited
```

### Permission Issues

```python
try:
    await notifier.send_email_notification(...)
except Exception as e:
    # Logged automatically
    # Service disabled if Forbidden error
    pass
```

## Integration Patterns

### Pattern 1: Long-Running Service

```python
class EmailProcessor:
    def __init__(self):
        self.notifier = DiscordNotifier()
    
    async def start(self):
        await self.notifier.start()
    
    async def stop(self):
        await self.notifier.stop()
    
    async def process_email(self, email):
        # ... classification logic ...
        await self.notifier.send_email_notification(...)

# Usage
processor = EmailProcessor()
await processor.start()
try:
    while True:
        email = await get_next_email()
        await processor.process_email(email)
finally:
    await processor.stop()
```

### Pattern 2: Filtered Notifications

```python
async def notify_if_important(email, notifier):
    """Only notify for important emails."""
    important_categories = ['Work', 'Finance', 'Security']
    
    if (email['category'] in important_categories and 
        email['confidence'] > 0.75):
        await notifier.send_email_notification(
            from_address=email['from'],
            subject=email['subject'],
            category=email['category'],
            email_id=email['id'],
            confidence=email['confidence']
        )
```

### Pattern 3: Batch Processing

```python
async def process_batch(emails, notifier):
    """Process multiple emails with delay."""
    for email in emails:
        await notifier.send_email_notification(...)
        await asyncio.sleep(0.5)  # Avoid rate limits
```

### Pattern 4: FastAPI Integration

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()
notifier = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global notifier
    notifier = DiscordNotifier()
    await notifier.start()
    yield
    # Shutdown
    await notifier.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/notify")
async def notify_email(email_data: dict):
    success = await notifier.send_email_notification(**email_data)
    return {"success": success}
```

## Troubleshooting

### Bot Not Connecting

**Check logs for:**
```
❌ Discord notifications disabled (no DISCORD_BOT_TOKEN)
```

**Solution**: Add `DISCORD_BOT_TOKEN` to `.env`

---

```
❌ Discord notifications disabled (no DISCORD_CHANNEL_ID)
```

**Solution**: Add `DISCORD_CHANNEL_ID` to `.env` (must be numeric)

---

```
❌ Invalid Discord bot token
```

**Solution**: 
1. Go to Discord Developer Portal
2. Bot section → Reset Token
3. Copy new token to `.env`

### Bot Not Sending Messages

**Check logs for:**
```
❌ Bot lacks permissions to send messages in channel
```

**Solution**:
1. Right-click channel → Edit Channel → Permissions
2. Add your bot role
3. Enable "Send Messages" and "Embed Links"

---

```
❌ Channel no longer exists
```

**Solution**: Update `DISCORD_CHANNEL_ID` with valid channel

### Rate Limit Issues

```
⚠️ Discord rate limit hit, retrying in Xs
```

**Solution**: This is automatic, but if persistent:
- Reduce notification frequency
- Increase delay between notifications
- Use batch processing with sleep

### Connection Drops

```
⚠️ Discord bot disconnected
Connection lost, retrying...
```

**Solution**: Automatic reconnection, but check:
- Network stability
- Discord service status
- Bot token validity

## Monitoring

### Statistics

```python
stats = notifier.get_stats()
print(stats)
# {
#     'enabled': True,
#     'connected': True,
#     'ready': True,
#     'rate_limit_hits': 3,
#     'reconnect_attempts': 0,
#     'channel_id': 1234567890,
#     'channel_name': 'email-notifications'
# }
```

### Logging

Set log level in your application:

```python
import logging
logging.getLogger('DiscordNotifier').setLevel(logging.DEBUG)
```

Logs include:
- Connection events
- Message send status
- Rate limit warnings
- Error details

## Testing

### Run Examples

```bash
python examples/discord_notifier_example.py
```

This runs 5 comprehensive examples:
1. Basic notification
2. Context manager usage
3. One-shot notification
4. Error handling
5. Integration pattern

### Manual Test

```python
import asyncio
from src.Services.notifications.DiscordNotifier import send_notification

asyncio.run(send_notification(
    from_address="test@example.com",
    subject="Test Notification",
    category="Work",
    email_id="test-001"
))
```

Check your Discord channel for the notification!

## Performance

- **Latency**: ~100-200ms per notification (network dependent)
- **Throughput**: ~5 notifications/second (respecting rate limits)
- **Memory**: ~50MB (discord.py client)
- **CPU**: Minimal (<1% on modern hardware)

## Security

### Bot Token Security

❌ **Never** commit `.env` to version control  
❌ **Never** hardcode tokens in source  
✅ **Use** environment variables  
✅ **Rotate** tokens periodically  
✅ **Limit** bot permissions to minimum required  

### Permissions

Minimum required permissions:
- Send Messages
- Embed Links

Optional permissions:
- Read Message History (for context)

## Production Checklist

- [ ] Bot token in `.env`, not hardcoded
- [ ] Channel ID configured and valid
- [ ] Bot invited to server with correct permissions
- [ ] Error logging configured
- [ ] Rate limit handling tested
- [ ] Graceful shutdown implemented
- [ ] Connection recovery tested
- [ ] Notification filtering logic in place
- [ ] Monitoring/statistics collection active
- [ ] Backup notification method available

## FAQ

**Q: Can I use multiple channels?**  
A: Yes, create multiple `DiscordNotifier` instances with different `DiscordConfig` objects specifying different channel IDs.

**Q: How do I customize embed colors?**  
A: Modify `CATEGORY_COLORS` dict in `DiscordNotifier` class.

**Q: Can I send to multiple servers?**  
A: Yes, but you need separate bot tokens per server (or proper OAuth2 setup).

**Q: What's the message size limit?**  
A: Discord embeds have these limits:
- Title: 256 chars
- Description: 4096 chars
- Field value: 1024 chars
- Total: 6000 chars across all fields

The notifier automatically truncates to stay within limits.

**Q: How do I add attachments?**  
A: Discord API supports file attachments, but this implementation focuses on embeds. For files, extend the `send_email_notification` method to accept a `files` parameter.

**Q: Can I @ mention users?**  
A: Yes, add `content=f"<@{user_id}>"` parameter to the `channel.send()` call. You'll need to enable mentions in embed settings.

## Support

For issues:
1. Check logs for error messages
2. Verify `.env` configuration
3. Test with `examples/discord_notifier_example.py`
4. Check Discord bot status in Developer Portal

## License

Same as parent project.

"""Example usage for DiscordNotifier service.

This script demonstrates:
1. Basic notification sending
2. Context manager usage
3. Multiple notifications in a session
4. Error handling patterns
5. Statistics monitoring

Setup Required:
--------------
1. Install dependencies:
   pip install discord.py python-dotenv

2. Create .env file with:
   DISCORD_BOT_TOKEN=your_bot_token_here
   DISCORD_CHANNEL_ID=1234567890123456789
   DISCORD_APP_URL=https://yourapp.com/emails

3. Set up Discord bot (see DiscordNotifier.py docstring for full instructions)
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Services.notifications.DiscordNotifier import (
    DiscordNotifier,
    DiscordNotifierContext,
    send_notification
)


# ======================== Example 1: Basic Usage ======================== #

async def example_basic():
    """Basic notification sending."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Notification")
    print("=" * 60)
    
    notifier = DiscordNotifier()
    
    if not notifier.enabled:
        print("❌ Discord notifications not enabled. Check your .env configuration.")
        return
    
    # Start the bot
    started = await notifier.start()
    if not started:
        print("❌ Failed to start Discord bot")
        return
    
    print("✅ Discord bot started")
    
    try:
        # Send a notification
        success = await notifier.send_email_notification(
            from_address="client@example.com",
            subject="Important Project Update - Q4 2025",
            category="Work",
            email_id="msg-12345",
            confidence=0.92,
            preview="Hi team, I wanted to provide an update on our Q4 roadmap...",
            timestamp=datetime.utcnow()
        )
        
        if success:
            print("✅ Notification sent successfully")
        else:
            print("❌ Failed to send notification")
        
        # Get stats
        stats = notifier.get_stats()
        print("\nService Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    finally:
        # Always cleanup
        await notifier.stop()
        print("\n✅ Discord bot stopped")


# ======================== Example 2: Context Manager ======================== #

async def example_context_manager():
    """Using context manager for automatic cleanup."""
    print("\n" + "=" * 60)
    print("Example 2: Context Manager Usage")
    print("=" * 60)
    
    async with DiscordNotifierContext() as notifier:
        if not notifier.enabled:
            print("❌ Discord notifications not enabled")
            return
        
        print("✅ Discord bot started (auto-managed)")
        
        # Send multiple notifications
        emails = [
            {
                "from_address": "billing@shop.com",
                "subject": "Your order has shipped!",
                "category": "Shopping",
                "email_id": "msg-67890",
                "confidence": 0.88,
                "preview": "Great news! Your order #98765 is on its way.",
            },
            {
                "from_address": "noreply@bank.com",
                "subject": "Account Statement - October 2025",
                "category": "Finance",
                "email_id": "msg-11111",
                "confidence": 0.95,
                "preview": "Your monthly statement is now available.",
                "metadata": {"account": "****1234", "balance": "$5,432.10"}
            },
            {
                "from_address": "alerts@security.com",
                "subject": "New login from Windows PC",
                "category": "Security",
                "email_id": "msg-22222",
                "confidence": 0.98,
                "preview": "We detected a new login to your account from Windows PC in New York.",
            }
        ]
        
        for email in emails:
            success = await notifier.send_email_notification(**email)
            status = "✅" if success else "❌"
            print(f"{status} Sent: {email['subject'][:50]}...")
            await asyncio.sleep(0.5)  # Small delay between messages
    
    print("\n✅ Discord bot stopped (auto-cleanup)")


# ======================== Example 3: One-Shot Notification ======================== #

async def example_oneshot():
    """Using convenience function for single notification."""
    print("\n" + "=" * 60)
    print("Example 3: One-Shot Notification")
    print("=" * 60)
    
    success = await send_notification(
        from_address="travel@airline.com",
        subject="Boarding Pass - Flight AA123",
        category="Travel",
        email_id="msg-33333",
        confidence=0.91,
        preview="Your boarding pass for flight AA123 to San Francisco is ready.",
        metadata={
            "flight": "AA123",
            "departure": "10:30 AM",
            "gate": "B7"
        }
    )
    
    if success:
        print("✅ One-shot notification sent successfully")
    else:
        print("❌ Failed to send one-shot notification")


# ======================== Example 4: Error Handling ======================== #

async def example_error_handling():
    """Demonstrating error handling patterns."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    notifier = DiscordNotifier()
    
    if not notifier.enabled:
        print("❌ Service disabled - gracefully handling")
        return
    
    try:
        await notifier.start()
        
        # Try sending with missing required fields (should handle gracefully)
        try:
            success = await notifier.send_email_notification(
                from_address="",  # Empty - should handle
                subject="Test Email",
                category="Work",
                email_id="msg-test-1"
            )
            print(f"Empty from_address handled: {success}")
        except Exception as e:
            print(f"Caught exception: {e}")
        
        # Try with very long subject (should truncate)
        long_subject = "A" * 500
        success = await notifier.send_email_notification(
            from_address="test@example.com",
            subject=long_subject,
            category="Work",
            email_id="msg-test-2"
        )
        print(f"Long subject handled (truncated): {success}")
        
        # Try with invalid category (should use default color)
        success = await notifier.send_email_notification(
            from_address="test@example.com",
            subject="Test",
            category="NonExistentCategory",
            email_id="msg-test-3"
        )
        print(f"Invalid category handled: {success}")
        
    except Exception as e:
        print(f"Error during example: {e}")
    finally:
        await notifier.stop()


# ======================== Example 5: Integration Pattern ======================== #

async def example_integration():
    """Realistic integration pattern for email processing pipeline."""
    print("\n" + "=" * 60)
    print("Example 5: Integration Pattern")
    print("=" * 60)
    
    # Simulated email processing pipeline
    async def process_incoming_email(email_data: dict, notifier: DiscordNotifier):
        """Simulate processing an incoming email."""
        print(f"\nProcessing email from {email_data['from']}")
        
        # Simulate classification
        category = email_data.get('category', 'Unclassified')
        confidence = email_data.get('confidence', 0.5)
        
        # Only notify for high-confidence, important categories
        important_categories = ['Work', 'Finance', 'Security', 'Travel']
        
        if category in important_categories and confidence > 0.75:
            success = await notifier.send_email_notification(
                from_address=email_data['from'],
                subject=email_data['subject'],
                category=category,
                email_id=email_data['id'],
                confidence=confidence,
                preview=email_data.get('preview'),
                metadata=email_data.get('metadata')
            )
            
            if success:
                print(f"  ✅ Notification sent for {category} email")
            else:
                print(f"  ⚠️ Failed to send notification")
        else:
            print(f"  ℹ️ Skipped notification (category: {category}, confidence: {confidence:.2f})")
    
    # Simulated incoming emails
    incoming_emails = [
        {
            "id": "msg-001",
            "from": "boss@company.com",
            "subject": "Urgent: Q4 Budget Review",
            "category": "Work",
            "confidence": 0.95,
            "preview": "We need to review the Q4 budget by EOD tomorrow.",
            "metadata": {"priority": "high", "deadline": "2025-10-08"}
        },
        {
            "id": "msg-002",
            "from": "promo@store.com",
            "subject": "50% OFF Everything!",
            "category": "Promotional",
            "confidence": 0.99,
            "preview": "Limited time offer on all items.",
        },
        {
            "id": "msg-003",
            "from": "bank@secure.com",
            "subject": "Suspicious activity detected",
            "category": "Security",
            "confidence": 0.98,
            "preview": "We detected unusual activity on your account.",
            "metadata": {"severity": "high", "action_required": True}
        },
        {
            "id": "msg-004",
            "from": "friend@example.com",
            "subject": "Hey, how are you?",
            "category": "Personal",
            "confidence": 0.82,
            "preview": "Just wanted to catch up!",
        }
    ]
    
    async with DiscordNotifierContext() as notifier:
        if not notifier.enabled:
            print("❌ Discord notifications not enabled")
            return
        
        print("✅ Starting email processing pipeline...\n")
        
        for email in incoming_emails:
            await process_incoming_email(email, notifier)
            await asyncio.sleep(0.5)
        
        print("\n✅ Pipeline complete")
        
        # Show final stats
        stats = notifier.get_stats()
        print(f"\nTotal notifications sent: {len([e for e in incoming_emails if e['category'] in ['Work', 'Finance', 'Security', 'Travel'] and e['confidence'] > 0.75])}")
        print(f"Rate limit hits: {stats['rate_limit_hits']}")


# ======================== Main Runner ======================== #

async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("DISCORD NOTIFIER EXAMPLES")
    print("=" * 60)
    
    try:
        # Run each example
        await example_basic()
        await asyncio.sleep(1)
        
        await example_context_manager()
        await asyncio.sleep(1)
        
        await example_oneshot()
        await asyncio.sleep(1)
        
        await example_error_handling()
        await asyncio.sleep(1)
        
        await example_integration()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Check if discord.py is installed
    try:
        import discord
    except ImportError:
        print("❌ discord.py not installed. Install it with:")
        print("   pip install discord.py python-dotenv")
        sys.exit(1)
    
    # Run examples
    asyncio.run(main())

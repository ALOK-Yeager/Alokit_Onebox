import { WebClient } from '@slack/web-api';
import dotenv from 'dotenv';
import logger from './src/Services/utils/Logger';

// Load environment variables
dotenv.config();

async function testSlack() {
    const token = process.env.SLACK_API_TOKEN;
    if (!token) {
        logger.error('SLACK_API_TOKEN is not set in .env file');
        return;
    }

    try {
        logger.info('Testing Slack connection...');
        const client = new WebClient(token);

        // Test the connection by sending a message to #general
        logger.info('Attempting to send a test message to #general...');

        // First, try to send to #leads with chat:write scope
        const result = await client.chat.postMessage({
            channel: '#leads',
            text: '🧪 *Test Message* from Onebox Aggregator\n_This is a test of the notification system._',
            unfurl_links: false,
            unfurl_media: false
        });

        if (result.ok) {
            logger.info('✅ Slack test successful! Message sent to #general');
            logger.debug('Message details:', {
                channel: result.channel,
                ts: result.ts,
                message: result.message
            });
        } else {
            logger.error('❌ Slack test failed:', result.error);
            if (result.error === 'channel_not_found') {
                logger.info('💡 Make sure to:\n1. Invite the bot to #general channel\n2. Or specify a channel where the bot is already a member');
            }
        }
    } catch (error) {
        logger.error('❌ Slack test failed:', error);
    }
}

// Run the test
testSlack();

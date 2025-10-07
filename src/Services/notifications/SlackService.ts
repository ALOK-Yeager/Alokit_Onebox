import { WebClient } from '@slack/web-api';
import { logger } from '../utils/Logger';

export class SlackService {
    private client: WebClient | null = null;
    private enabled: boolean = false;

    constructor() {
        const token = process.env.SLACK_API_TOKEN;
        if (token) {
            try {
                this.client = new WebClient(token);
                this.enabled = true;
                logger.info('✅ Slack notifications enabled');
            } catch (error) {
                logger.error('Failed to initialize Slack client:', error);
            }
        } else {
            logger.info('ℹ️ Slack notifications disabled (no SLACK_API_TOKEN)');
        }
    }

    async sendNotification(message: string, channel: string = '#leads'): Promise<boolean> {
        if (!this.enabled || !this.client) {
            return false;
        }

        try {
            // Ensure channel has # prefix
            const targetChannel = channel.startsWith('#') ? channel : `#${channel}`;

            // Try to post the message using available scopes
            const result = await this.client.chat.postMessage({
                channel: targetChannel,
                text: message,
                unfurl_links: false,
                unfurl_media: false
            });

            if (result.ok) {
                logger.debug('Slack notification sent successfully');
                return true;
            } else {
                logger.warn('Slack notification failed:', result.error);
                return false;
            }
        } catch (error) {
            logger.error('Failed to send Slack notification:', error);
            return false;
        }
    }

    public isEnabled(): boolean {
        return this.enabled;
    }
}

// For CommonJS compatibility
module.exports = { SlackService };

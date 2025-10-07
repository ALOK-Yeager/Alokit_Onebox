import fetch from 'node-fetch';
import { logger } from '../utils/Logger';

interface WebhookPayload {
    category: string;
    emailId: string;
    confidence?: number;
    metadata?: Record<string, any>;
}

export class WebhookService {
    private readonly url: string | null = null;
    private enabled: boolean = false;

    constructor() {
        this.url = process.env.WEBHOOK_URL || null;
        if (this.url) {
            this.enabled = true;
            logger.info('✅ Webhook notifications enabled');
        } else {
            logger.info('ℹ️ Webhook notifications disabled (no WEBHOOK_URL)');
        }
    }

    async triggerWebhook(data: WebhookPayload): Promise<boolean> {
        if (!this.enabled || !this.url) {
            return false;
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
            
            const response = await fetch(this.url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Onebox-Aggregator/1.0'
                },
                body: JSON.stringify({
                    ...data,
                    timestamp: new Date().toISOString()
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            if (response.ok) {
                logger.debug('Webhook triggered successfully');
                return true;
            } else {
                logger.warn(`Webhook failed with status ${response.status}:`, await response.text());
                return false;
            }
        } catch (error) {
            logger.error('Failed to trigger webhook:', error);
            return false;
        }
    }

    public isEnabled(): boolean {
        return this.enabled;
    }
}

// For CommonJS compatibility
module.exports = { WebhookService };

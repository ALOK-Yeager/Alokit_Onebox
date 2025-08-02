const Imap = require('imap');
const { logger } = require('../utils/Logger');

class ReconnectionManager {
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private isCleaningUp = false;

    constructor(
        private imap: any,
        private accountConfig: any,
        private reconnectCallback: () => Promise<void>,
        private failureCallback: () => void
    ) {
        this.setupReconnectionHandlers();
    }

    private setupReconnectionHandlers(): void {
        this.imap.once('error', (err: any) => {
            logger.error(`IMAP error for ${this.accountConfig.email}:`, err);
            this.handleConnectionIssue();
        });

        this.imap.once('end', () => {
            logger.info(`IMAP connection ended for ${this.accountConfig.email}`);
            this.handleConnectionIssue();
        });

        this.imap.once('close', () => {
            logger.info(`IMAP connection closed for ${this.accountConfig.email}`);
            this.handleConnectionIssue();
        });
    }

    private handleConnectionIssue(): void {
        if (this.isCleaningUp) return;

        // Only attempt reconnection if we were previously connected
        if (this.imap.state !== 'disconnected' && this.imap.state !== 'closed') {
            this.scheduleReconnect();
        }
    }

    public scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            logger.error(`Max reconnect attempts reached for ${this.accountConfig.email}`);
            this.cleanup();
            this.failureCallback();
            return;
        }

        // Exponential backoff with jitter
        const baseDelay = 1000; // 1 second
        const maxDelay = 30000; // 30 seconds
        const jitter = Math.random() * 1000; // Add randomness

        const delay = Math.min(
            baseDelay * Math.pow(2, this.reconnectAttempts) + jitter,
            maxDelay
        );

        this.reconnectAttempts++;

        logger.info(
            `Scheduling reconnect for ${this.accountConfig.email} in ${delay}ms ` +
            `(attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
        );

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }

        this.reconnectTimeout = setTimeout(async () => {
            try {
                await this.reconnectCallback();
            } catch (err) {
                logger.error(`Reconnect attempt failed for ${this.accountConfig.email}:`, err);
                this.scheduleReconnect();
            }
        }, delay);
    }

    public cleanup(): void {
        this.isCleaningUp = true;

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        // Remove all listeners to prevent memory leaks
        this.imap.removeAllListeners('ready');
        this.imap.removeAllListeners('error');
        this.imap.removeAllListeners('end');
        this.imap.removeAllListeners('close');
        this.imap.removeAllListeners('mail');

        logger.info(`Reconnection manager cleaned up for ${this.accountConfig.email}`);
    }
}

module.exports = { ReconnectionManager };

const Imap = require('imap');
const { logger } = require('../utils/Logger');
import type { AccountConfig } from './AccountConfig';

export class IdleManager {
    private isIdling = false;
    private noopTimer: NodeJS.Timeout | null = null;
    private serverType: 'gmail' | 'outlook' | 'other' = 'other';
    private noopInterval: number = 30 * 60 * 1000; // Default to 30 minutes

    constructor(
        private imap: any,
        private accountConfig: any,
        private onNewEmails: (numNewMsgs: number) => Promise<void>
    ) {
        this.setupServerDetection();
    }

    private setupServerDetection(): void {
        this.imap.once('ready', () => {
            const serverHost = (this.imap as any).config?.host || this.accountConfig.host || '';
            if (serverHost.includes('imap.gmail.com')) {
                this.serverType = 'gmail';
                this.noopInterval = 25 * 60 * 1000; // 25 minutes for Gmail
                logger.info(`Detected Gmail server for ${this.accountConfig.email}`);
            } else if (serverHost.includes('outlook') || serverHost.includes('office365')) {
                this.serverType = 'outlook';
                this.noopInterval = 15 * 60 * 1000; // 15 minutes for Outlook
                logger.info(`Detected Outlook server for ${this.accountConfig.email}`);
            } else {
                this.noopInterval = 30 * 60 * 1000; // 30 minutes for other servers
                logger.info(`Detected generic IMAP server for ${this.accountConfig.email}`);
            }
        });
    }

    public start(): void {
        if (this.isIdling) {
            logger.debug(`IDLE mode already active for ${this.accountConfig.email}`);
            return;
        }

        this.enterIdleMode();
    }

    private enterIdleMode(): void {
        this.imap.openBox('INBOX', true, (err: Error | null, box: any) => {
            if (err) {
                logger.error(`Error opening INBOX for ${this.accountConfig.email}:`, err);
                return;
            }

            this.isIdling = true;
            logger.info(`Entered IDLE mode for ${this.accountConfig.email}`);

            // Schedule NOOP to prevent server timeouts
            this.scheduleNoop();

            // Set up email notification handler
            this.imap.on('mail', (numNewMsgs: number) => {
                logger.info(`[IDLE DEBUG] 'mail' event fired for ${this.accountConfig.email} with numNewMsgs: ${numNewMsgs}`);
                logger.info(`[IDLE DEBUG] If you see this, the IMAP mail event is working!`);
                this.onNewEmails(numNewMsgs).catch(err => {
                    logger.error(`Error handling new emails for ${this.accountConfig.email}:`, err);
                });
            });
        });
    }

    private scheduleNoop(): void {
        if (this.noopTimer) {
            clearTimeout(this.noopTimer);
        }

        this.noopTimer = setTimeout(() => {
            if (this.isIdling) {
                logger.debug(`Sending NOOP for ${this.accountConfig.email}`);
                (this.imap as any)._send('NOOP', '', () => { });
                this.scheduleNoop();
            }
        }, this.noopInterval);
    }

    public stop(): void {
        if (!this.isIdling) return;

        this.isIdling = false;

        if (this.noopTimer) {
            clearTimeout(this.noopTimer);
            this.noopTimer = null;
        }

        try {
            this.imap.removeAllListeners('mail');
            logger.info(`IDLE mode stopped for ${this.accountConfig.email}`);
        } catch (err) {
            logger.warn(`Error stopping IDLE mode for ${this.accountConfig.email}:`, err);
        }
    }

}
// For CommonJS compatibility
module.exports = { IdleManager };
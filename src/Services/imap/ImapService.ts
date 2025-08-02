import Imap from 'imap';
import { EventEmitter } from 'events';
import { logger } from '../utils/Logger';
import { AccountConfig } from './AccountConfig';
import { Email } from './Email';
import { IdleManager } from './IdleManager';
import { ReconnectionManager } from './ReconnectionManager';
import { SyncManager } from './SyncManager';
import { EmailParser } from './EmailParser';

export class ImapService {
    private imap: Imap | null = null;
    private idleManager: IdleManager | null = null;
    private reconnectionManager: ReconnectionManager | null = null;
    private syncManager: SyncManager | null = null;
    private emailParser: EmailParser;
    private isInitialized = false;
    private eventEmitter = new EventEmitter();
    private cleanupCallbacks: Array<() => void> = [];
    private serverType: 'gmail' | 'outlook' | 'other' = 'other';
    private noopInterval: number = 30 * 60 * 1000; // Default 30 minutes

    constructor(
        private accountConfig: AccountConfig,
        private onEmailReceived: (email: Email) => void,
        private onEmailIndexed: (emailId: string) => void
    ) {
        this.emailParser = new EmailParser();
        this.setupCleanup();
    }

    public async initialize(): Promise<void> {
        if (this.isInitialized) {
            logger.info(`IMAP service for ${this.accountConfig.email} is already initialized`);
            return;
        }

        logger.info(`Initializing IMAP service for ${this.accountConfig.email}`);

        try {
            this.imap = new Imap({
                user: this.accountConfig.email,
                password: this.accountConfig.password,
                host: this.accountConfig.host,
                port: this.accountConfig.port,
                tls: this.accountConfig.tls,
                tlsOptions: {
                    rejectUnauthorized: false
                },
                authTimeout: 30000,
                keepalive: {
                    interval: 10000,
                    idleInterval: 300000,
                    forceNoop: true
                }
            });

            this.reconnectionManager = new ReconnectionManager(
                this.imap,
                this.accountConfig,
                this.initialize.bind(this),
                this.handleConnectionFailure.bind(this)
            );

            this.idleManager = new IdleManager(
                this.imap,
                this.accountConfig,
                this.handleNewEmails.bind(this)
            );

            this.syncManager = new SyncManager(
                this.imap,
                this.accountConfig,
                this.emailParser,
                this.onEmailReceived,
                this.onEmailIndexed
            );

            this.setupEventHandlers();
            this.imap.connect();

            this.isInitialized = true;
            logger.info(`IMAP service initialized for ${this.accountConfig.email}`);
        } catch (err) {
            logger.error(`Failed to initialize IMAP service for ${this.accountConfig.email}:`, err);
            this.handleConnectionFailure();
            throw err;
        }
    }

    private setupEventHandlers(): void {
        if (!this.imap) return;

        this.imap.once('ready', () => {
            logger.info(`IMAP connection ready for ${this.accountConfig.email}`);

            // Detect server type for proper NOOP intervals
            this.detectServerType();

            // Ensure IMAP connection exists before opening mailbox
            if (!this.imap) {
                logger.error(`IMAP connection is null for ${this.accountConfig.email}`);
                this.handleConnectionFailure();
                return;
            }

            this.imap.openBox('INBOX', false, (err: Error, box: any) => {
                if (err) {
                    logger.error(`Error opening INBOX for ${this.accountConfig.email}:`, err);
                    this.handleConnectionFailure();
                    return;
                }
                logger.info(`INBOX opened for ${this.accountConfig.email}`);

                // Schedule historical sync after a brief delay to avoid overwhelming connection
                setTimeout(async () => {
                    try {
                        await this.syncManager?.fetchHistoricalEmails();
                        this.idleManager?.start();
                        this.eventEmitter.emit('ready');
                    } catch (err) {
                        logger.error(`Error during IMAP ready state for ${this.accountConfig.email}:`, err);
                        this.handleConnectionFailure();
                    }
                }, 2000);
            });
        });

        this.imap.once('error', (err: any) => {
            logger.error(`IMAP error for ${this.accountConfig.email}:`, err);
            this.handleConnectionFailure();
        });
    }

    private detectServerType(): void {
        // Use type assertion to access serverName
        const serverName = (this.imap as any)?.serverName || '';
        if (serverName.includes('imap.gmail.com')) {
            this.serverType = 'gmail';
            this.noopInterval = 25 * 60 * 1000; // 25 minutes for Gmail
            logger.info(`Detected Gmail server for ${this.accountConfig.email}`);
        } else if (serverName.includes('outlook') || serverName.includes('office365')) {
            this.serverType = 'outlook';
            this.noopInterval = 15 * 60 * 1000; // 15 minutes for Outlook
            logger.info(`Detected Outlook server for ${this.accountConfig.email}`);
        } else {
            this.serverType = 'other';
            this.noopInterval = 30 * 60 * 1000; // 30 minutes for other servers
            logger.info(`Detected generic IMAP server for ${this.accountConfig.email}`);
        }
        // Remove setNoopInterval call if not implemented in IdleManager
    }

    private async handleNewEmails(numNewMsgs: number): Promise<void> {
        logger.info(`New email(s) received for ${this.accountConfig.email}: ${numNewMsgs}`);
        try {
            await this.syncManager?.fetchNewEmails(numNewMsgs);
        } catch (err) {
            logger.error(`Error fetching new emails for ${this.accountConfig.email}:`, err);
        }
    }

    private handleConnectionFailure(): void {
        logger.warn(`Connection failure for ${this.accountConfig.email}. Attempting reconnection...`);
        this.reconnectionManager?.scheduleReconnect();
        this.eventEmitter.emit('connection-failed');
    }

    public on(event: 'ready' | 'connection-failed' | 'email-received', listener: (...args: any[]) => void): void {
        this.eventEmitter.on(event, listener);
    }

    public removeListener(event: 'ready' | 'connection-failed' | 'email-received', listener: (...args: any[]) => void): void {
        this.eventEmitter.removeListener(event, listener);
    }

    public isConnected(): boolean {
        return this.isInitialized && !!this.imap && this.imap.state === 'connected';
    }

    public getServerType(): 'gmail' | 'outlook' | 'other' {
        return this.serverType;
    }

    public getNoopInterval(): number {
        return this.noopInterval;
    }

    public async disconnect(): Promise<void> {
        logger.info(`Disconnecting IMAP service for ${this.accountConfig.email}`);

        // Remove all listeners first
        this.eventEmitter.removeAllListeners();

        // Stop idle mode
        this.idleManager?.stop();

        // Clean up all resources
        this.cleanupCallbacks.forEach(callback => callback());
        this.cleanupCallbacks = [];

        // End the IMAP connection
        if (this.imap && this.imap.state !== 'disconnected') {
            try {
                this.imap.end();
                logger.info(`IMAP connection ended for ${this.accountConfig.email}`);
            } catch (err) {
                logger.warn(`Error ending IMAP connection for ${this.accountConfig.email}:`, err);
            }
        }

        this.isInitialized = false;
        this.imap = null;
    }

    private setupCleanup(): void {
        // Cleanup idle manager
        this.cleanupCallbacks.push(() => {
            if (this.idleManager) {
                this.idleManager.stop();
                this.idleManager = null;
            }
        });

        // Cleanup reconnection manager
        this.cleanupCallbacks.push(() => {
            if (this.reconnectionManager) {
                this.reconnectionManager.cleanup();
                this.reconnectionManager = null;
            }
        });

        // Cleanup sync manager
        this.cleanupCallbacks.push(() => {
            this.syncManager = null;
        });
    }
}
// For CommonJS compatibility
module.exports = { ImapService };
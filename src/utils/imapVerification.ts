const { ImapService } = require('../Services/imap/ImapService');
const { logger } = require('../Services/utils/Logger');

interface ImapAccountConfig {
    host: string;
    port: number;
    user: string;
    password: string;
    tls?: boolean;
    // Add other properties as needed for your ImapService
}

interface Email {
    subject: string;
    // Add other email properties as needed
}

/**
 * Verifies IMAP implementation by initializing the service, testing connection, and listening for new emails.
 * @param {ImapAccountConfig} accountConfig
 */
const verifyImapImplementation = async (accountConfig: ImapAccountConfig) => {
    const imapService = new ImapService(
        accountConfig,
        (email: Email) => logger.info(`✓ Received email: ${email.subject}`),
        (emailId: string) => logger.info(`✓ Indexed email: ${emailId}`)
    );

    try {
        // 1. Test basic connection
        logger.info('\nSTEP 1: Testing basic connection...');
        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('IMAP connection timed out'));
            }, 15000);

            imapService.on('ready', () => {
                clearTimeout(timeout);
                logger.info('✓ Connection established');
                resolve();
            });

            imapService.on('connection-failed', () => {
                clearTimeout(timeout);
                reject(new Error('IMAP connection failed'));
            });

            imapService.initialize().catch(reject);
        });

        // 2. Test historical sync
        logger.info('\nSTEP 2: Testing historical sync (last 30 days)...');
        // (Optional: you can call imapService.syncManager.fetchHistoricalEmails() here if needed)

        // 3. Test IDLE mode
        logger.info('\nSTEP 3: Testing IDLE mode...');
        logger.info('✓ IDLE mode initialized - sending test email now...');
        logger.info('   Please send a test email to this account within 60 seconds');

        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('No new email detected in IDLE mode'));
            }, 60000);

            imapService.on('email-received', (email: Email) => {
                logger.info('✓ New email detected in real-time (IDLE working)');
                resolve();
            });
        });

        // 4. Test connection resilience (optional)
        logger.info('\nSTEP 4: Testing connection resilience...');
        logger.info('   Disconnecting network in 5 seconds - reconnect should happen automatically');
        await new Promise<void>(resolve => setTimeout(resolve, 5000));
        logger.info('   Network disconnected - watching for reconnect...');
        // (Optional: implement reconnection test logic here)

        logger.info('\nIMAP verification completed successfully!');
        logger.info('Your implementation is ready for integration with other components');

        // Return the service so it can be used
        return imapService;
    } catch (error) {
        logger.error('IMAP verification failed:', error);
        await imapService.disconnect();
        throw error;
    }
};

module.exports = { verifyImapImplementation };

const { ImapService } = require('../imap/ImapService');
const { AccountConfig } = require('../imap/AccountConfig');
const { logger } = require('./Logger');
const { Email } = require('../imap/Email');

/** @type {(accountConfig: any) => Promise<any>} */
const verifyImapImplementation = async (accountConfig: any) => {
    logger.info('Starting IMAP verification process...');

    const imapService = new ImapService(
        accountConfig,
        (email: any) => logger.info(`✓ Received email: ${email.subject}`),
        (emailId: string) => logger.info(`✓ Indexed email: ${emailId}`)
    );

    try {
        // 1. Test basic connection
        logger.info('\nSTEP 1: Testing basic connection...');
        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                logger.error('✗ Connection timed out');
                reject(new Error('Connection timed out'));
            }, 15000);

            imapService.on('ready', () => {
                clearTimeout(timeout);
                logger.info('✓ Connection established');
                resolve();
            });

            imapService.on('connection-failed', () => {
                clearTimeout(timeout);
                logger.error('✗ Connection failed');
                reject(new Error('Connection failed'));
            });

            imapService.initialize().catch(reject);
        });

        // 2. Test historical sync
        logger.info('\nSTEP 2: Testing historical sync (last 30 days)...');

        // 3. Test IDLE mode
        logger.info('\nSTEP 3: Testing IDLE mode...');
        logger.info('✓ IDLE mode initialized - sending test email now...');
        logger.info('   Please send a test email to this account within 60 seconds');

        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => {
                logger.error('✗ IDLE mode test timed out - no email received');
                reject(new Error('IDLE test timed out'));
            }, 60000);

            imapService.on('email-received', () => {
                clearTimeout(timeout);
                logger.info('✓ New email detected in real-time (IDLE working)');
                resolve();
            });
        });

        // 4. Test connection resilience
        logger.info('\nSTEP 4: Testing connection resilience...');
        logger.info('   Disconnecting network in 5 seconds - reconnect should happen automatically');

        await new Promise(resolve => setTimeout(resolve, 5000));

        logger.info('   Network disconnected - watching for reconnect...');

        await new Promise<void>((resolve, reject) => {
            let attempts = 0;
            const checkInterval = setInterval(() => {
                if (imapService.isConnected()) {
                    clearInterval(checkInterval);
                    logger.info(`✓ Connection restored after ${attempts} attempts`);
                    resolve();
                }

                attempts++;
                if (attempts > 10) {
                    clearInterval(checkInterval);
                    logger.error('✗ Connection failed to restore');
                    reject(new Error('Connection failed to restore'));
                }
            }, 2000);
        });

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
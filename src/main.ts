const dotenv = require('dotenv');
const path = require('path');
const { verifyImapImplementation } = require('./utils/imapVerification');
const { logger } = require('./services/utils/logger');
const { AccountConfig } = require('./services/imap/AccountConfig');

// Load environment variables from .env file
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// Validate required environment variables
const requiredEnvVars = [
    'IMAP_SERVER',
    'IMAP_PORT',
    'IMAP_USER',
    'IMAP_PASSWORD',
    'IMAP_TLS'
] as const;

function validateEnv() {
    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
        throw new Error(
            `Missing required environment variables: ${missingVars.join(', ')}\n` +
            'Please check your .env file and make sure all required variables are set.'
        );
    }
}

// Validate environment variables before starting the application
validateEnv();

// Create account configuration
const accountConfig = {
    id: 'account-1',
    email: process.env.IMAP_USER!,
    password: process.env.IMAP_PASSWORD!,
    host: process.env.IMAP_SERVER!,
    port: parseInt(process.env.IMAP_PORT!, 10),
    tls: (process.env.IMAP_TLS || 'true').toLowerCase() === 'true'
};

// Main application logic
async function main() {
    logger.info('Environment loaded successfully');
    logger.info('IMAP Server:', accountConfig.host);

    // Verify IMAP implementation
    try {
        logger.info('\nStarting IMAP verification process...');
        const imapService = await verifyImapImplementation(accountConfig);

        logger.info('\nIMAP service is ready for integration with other components');
        logger.info('Next steps:');
        logger.info('1. Integrate with Elasticsearch for storage');
        logger.info('2. Implement AI categorization service');
        logger.info('3. Build frontend interface');

        // Keep the process running and listening for new emails
        logger.info('\nPress Ctrl+C to exit');

        // Prevent the process from exiting
        setInterval(() => { }, 1000 * 60 * 60);

        process.on('SIGINT', async () => {
            logger.info('\nShutting down...');
            await imapService.disconnect();
            process.exit(0);
        });
    } catch (error) {
        logger.error('IMAP verification failed:', error);
        process.exit(1);
    }
}

main().catch(error => {
    logger.error('Application error:', error);
    process.exit(1);
});
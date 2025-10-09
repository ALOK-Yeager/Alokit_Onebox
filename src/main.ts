const dotenv = require('dotenv');
const path = require('path');
const express = require('express');
const { logger } = require('./Services/utils/Logger');
const { AccountConfig } = require('./Services/imap/AccountConfig');
const emailRoutes = require('./routes/emailRoutes');
const { ImapService } = require('./Services/imap/ImapService');
const { DualIndexingAdapter } = require('./Services/search/DualIndexingAdapter');
import { Email } from './Services/imap/Email';

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

    // Use DualIndexingAdapter for email indexing
    const indexingService = new DualIndexingAdapter();

    // Set up Express server for API endpoints
    const app = express();
    app.use(express.json({ limit: '50mb' })); // For large email content
    app.use('/api/emails', emailRoutes);

    // Start API server
    const PORT = process.env.PORT || 3000;
    const server = app.listen(PORT, () => {
        logger.info(`🚀 API server running on port ${PORT}`);
        logger.info(`📧 Classification endpoint: http://localhost:${PORT}/api/emails/classify`);
        logger.info(`🔍 Search endpoint: http://localhost:${PORT}/api/emails/search`);
    });

    // Define email processing callbacks
    const onEmailReceived = async (email: Email) => {
        try {
            logger.info(`Received email: ${email.subject}`);
            await indexingService.indexEmail(email);
        } catch (error) {
            logger.error(`Failed to index email ${email.id}:`, error);
        }
    };

    const onEmailIndexed = (emailId: string) => {
        logger.info(`Successfully indexed email: ${emailId}`);
    };

    // Initialize IMAP service
    const imapService = new ImapService(accountConfig, onEmailReceived, onEmailIndexed);

    try {
        logger.info('\nStarting IMAP service...');
        await imapService.initialize();
        logger.info('\nIMAP service is running and listening for new emails.');

        // Keep the process running
        logger.info('\nPress Ctrl+C to exit');
        process.on('SIGINT', async () => {
            logger.info('\nShutting down...');
            server.close();
            await imapService.disconnect();
            process.exit(0);
        });
    } catch (error) {
        logger.error('Failed to start IMAP service:', error);
        process.exit(1);
    }
}

main().catch(error => {
    logger.error('Application error:', error);
    process.exit(1);
});

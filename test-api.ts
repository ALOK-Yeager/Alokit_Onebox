import express from 'express';
import emailRoutes from './src/routes/emailRoutes';
import logger from './src/Services/utils/Logger';

const testAPI = async () => {
    const app = express();
    app.use(express.json());
    app.use('/api/emails', emailRoutes);

    const PORT = 3001; // Different port to avoid conflicts

    const server = app.listen(PORT, () => {
        logger.info(`🚀 Test API server running on port ${PORT}`);
        logger.info(`Test the API with: http://localhost:${PORT}/api/emails/search?q=test&from=0&size=10`);
        logger.info('Press Ctrl+C to stop the test server');
    });

    // Handle graceful shutdown
    process.on('SIGINT', () => {
        logger.info('Shutting down test API server...');
        server.close(() => {
            logger.info('Test API server stopped');
            process.exit(0);
        });
    });
};

testAPI().catch((error) => {
    logger.error('Failed to start test API:', error);
    process.exit(1);
});

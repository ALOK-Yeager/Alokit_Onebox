import express from 'express';
import { EmailIndexingService } from '../Services/search/EmailIndexingService';
import { ElasticsearchService } from '../Services/search/ElasticsearchService';
import { EmailClassificationService } from '../Services/ai/EmailClassificationService';
import logger from '../Services/utils/Logger';

const router = express.Router();

// Initialize services - fallback to ElasticsearchService if EmailIndexingService fails
let searchService: EmailIndexingService | ElasticsearchService;

try {
    // Try to initialize EmailIndexingService with dual indexing
    searchService = new EmailIndexingService({
        enableVectorDB: process.env.ENABLE_VECTORDB !== 'false',
        enableElasticsearch: true,
        enableTransactionSafety: process.env.TRANSACTION_SAFETY !== 'false',
        batchSize: parseInt(process.env.INDEXING_BATCH_SIZE || '20'),
        vectorDBEndpoint: process.env.VECTORDB_ENDPOINT || 'http://localhost:8001'
    });
    logger.info('Initialized EmailIndexingService with dual indexing support');
} catch (error) {
    // Fallback to original ElasticsearchService for backward compatibility
    logger.warn('Failed to initialize EmailIndexingService, falling back to ElasticsearchService:', error);
    searchService = new ElasticsearchService();
}

const classificationService = new EmailClassificationService();

// Search emails (unchanged API for backward compatibility)
router.get('/search', async (req, res) => {
    try {
        const { q, account, folder, category } = req.query as Record<string, any>;

        // Both services implement the same search interface
        const result = await searchService.search(
            q as string || '',
            account as string,
            folder as string,
            category as string
        );

        res.json(result);
    } catch (error) {
        logger.error('Search API error:', error);
        res.status(500).json({ error: 'Search failed' });
    }
});

// Get email by ID (unchanged API for backward compatibility)
router.get('/:id', async (req, res) => {
    try {
        const resp = await searchService.getEmailById(req.params.id);
        const source = resp._source as Record<string, any> || {};
        res.json({ id: resp._id, ...source });
    } catch (error) {
        logger.error('Get email by ID error:', error);
        res.status(404).json({ error: 'Email not found' });
    }
});

// Classify email text (unchanged)
router.post('/classify', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text || typeof text !== 'string') {
            return res.status(400).json({
                error: 'Missing or invalid email text. Please provide a "text" field in the request body.'
            });
        }

        if (text.trim().length < 5) {
            return res.status(400).json({
                error: 'Email text too short for classification (minimum 5 characters)'
            });
        }

        const result = await classificationService.classifyEmail(text);

        res.json({
            text: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
            category: result.category,
            confidence: result.confidence,
            error: result.error,
            timestamp: new Date().toISOString(),
            serviceAvailable: classificationService.isServiceAvailable()
        });

    } catch (error) {
        logger.error('Classification API error:', error);
        res.status(500).json({
            error: 'Classification failed',
            details: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// NEW: Batch indexing endpoint for efficiency
router.post('/index-batch', async (req, res) => {
    try {
        const { emails } = req.body;

        if (!Array.isArray(emails) || emails.length === 0) {
            return res.status(400).json({
                error: 'Invalid request. Provide an array of emails to index.'
            });
        }

        // Only available with EmailIndexingService
        if (!(searchService instanceof EmailIndexingService)) {
            return res.status(501).json({
                error: 'Batch indexing not available. EmailIndexingService required.'
            });
        }

        logger.info(`Starting batch indexing of ${emails.length} emails`);

        const result = await searchService.indexEmails(emails);

        res.json({
            success: result.totalSuccessful > 0,
            processed: result.totalProcessed,
            successful: result.totalSuccessful,
            failed: result.totalFailed,
            processingTimeMs: result.totalProcessingTimeMs,
            elasticsearchSuccessful: result.elasticsearchSuccessful,
            vectorDBSuccessful: result.vectorDBSuccessful,
            errors: result.errors.slice(0, 10) // Limit error details
        });

    } catch (error) {
        logger.error('Batch indexing API error:', error);
        res.status(500).json({
            error: 'Batch indexing failed',
            details: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// NEW: Service status and statistics
router.get('/service/status', async (req, res) => {
    try {
        const isEmailIndexingService = searchService instanceof EmailIndexingService;

        if (isEmailIndexingService) {
            const indexingService = searchService as EmailIndexingService;
            const stats = indexingService.getStats();
            const health = await indexingService.healthCheck();

            res.json({
                service: 'EmailIndexingService',
                dualIndexing: true,
                health,
                stats,
                features: {
                    vectorDB: stats.config.enableVectorDB,
                    elasticsearch: stats.config.enableElasticsearch,
                    transactionSafety: stats.config.enableTransactionSafety,
                    batchProcessing: true
                }
            });
        } else {
            res.json({
                service: 'ElasticsearchService',
                dualIndexing: false,
                health: { elasticsearch: true, vectorDB: false, overall: true },
                features: {
                    vectorDB: false,
                    elasticsearch: true,
                    transactionSafety: false,
                    batchProcessing: false
                }
            });
        }

    } catch (error) {
        logger.error('Service status error:', error);
        res.status(500).json({
            error: 'Failed to get service status',
            details: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// NEW: Health check endpoint
router.get('/health', async (req, res) => {
    try {
        if (searchService instanceof EmailIndexingService) {
            const health = await searchService.healthCheck();
            res.json({
                status: health.overall ? 'healthy' : 'degraded',
                services: health
            });
        } else {
            // Simple health check for ElasticsearchService
            await searchService.search('', undefined, undefined, undefined);
            res.json({
                status: 'healthy',
                services: { elasticsearch: true, vectorDB: false, overall: true }
            });
        }
    } catch (error) {
        logger.error('Health check error:', error);
        res.status(503).json({
            status: 'unhealthy',
            error: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// ES module export
export default router;

// CommonJS export for compatibility  
module.exports = router;
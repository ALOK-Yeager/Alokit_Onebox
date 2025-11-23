import express from 'express';
import { ElasticsearchService } from '../Services/search/ElasticsearchService';
import { EmailClassificationService } from '../Services/ai/EmailClassificationService';
import logger from '../Services/utils/Logger';
import { DualIndexingAdapter } from '../Services/search/DualIndexingAdapter';

const router = express.Router();
const esService = new ElasticsearchService();
const dualIndexingAdapter = new DualIndexingAdapter();
const classifierEnabled = (process.env.ENABLE_CLASSIFIER || 'false').toLowerCase() === 'true';
const classificationService = classifierEnabled ? new EmailClassificationService() : null;

if (!classifierEnabled) {
    logger.info('Classification API disabled via ENABLE_CLASSIFIER flag');
}

// Hybrid Search Endpoint
router.get('/search', async (req, res) => {
    const { q, type = 'hybrid', category, categories } = req.query as Record<string, any>;

    try {
        if (!q) {
            return res.status(400).json({ error: 'Search query (q) is required' });
        }

        let results: any[] = [];

        // Parse categories if provided as comma-separated string
        let categoryList: string[] = [];
        if (categories) {
            categoryList = categories.split(',').map((c: string) => c.trim()).filter((c: string) => c.length > 0);
        } else if (category) {
            categoryList = [category];
        }

        if (type === 'keyword' || type === 'hybrid') {
            const keywordResults = await esService.search(q, undefined, undefined, undefined, categoryList);
            results.push(...keywordResults.emails.map((email: any) => ({
                ...email,
                match_type: 'keyword'
            })));
        }

        if (type === 'semantic' || type === 'hybrid') {
            const semanticResults = await dualIndexingAdapter.search(q);
            if (semanticResults && Array.isArray(semanticResults.emails)) {
                results.push(...semanticResults.emails.map((result: any) => ({
                    ...result,
                    match_type: 'semantic'
                })));
            }
        }

        // Deduplicate results, preferring higher scores
        const uniqueResults = Array.from(
            results.reduce((map, item) => {
                if (!map.has(item.id) || (item.score && map.get(item.id).score < item.score)) {
                    map.set(item.id, item);
                }
                return map;
            }, new Map<string, any>()).values()
        );

        // Sort by score
        uniqueResults.sort((a: any, b: any) => (b.score || 0) - (a.score || 0));

        res.json({
            query: q,
            search_type: type,
            count: uniqueResults.length,
            results: uniqueResults
        });

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        const errorStack = error instanceof Error ? error.stack : '';
        logger.error('Hybrid search API error:', { error: errorMessage, stack: errorStack });
        res.status(500).json({
            error: 'Search failed',
            details: errorMessage,
            type: type || 'hybrid',
            query: q || ''
        });
    }
});

// Get email by ID
router.get('/:id', async (req, res) => {
    try {
        const resp = await esService.getEmailById(req.params.id);
        if (!resp) {
            return res.status(404).json({ error: 'Email not found' });
        }
        const source = (resp._source as Record<string, any>) || {};
        res.json({ id: resp._id, ...source });
    } catch (error) {
        logger.error('Get email by ID error:', error);
        res.status(404).json({ error: 'Email not found' });
    }
});

// Classify email text
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

        const activeClassifier = classificationService;
        if (!classifierEnabled || !activeClassifier) {
            return res.status(503).json({
                error: 'Email classification disabled',
                serviceAvailable: false
            });
        }

        const result = await activeClassifier.classifyEmail(text);

        res.json({
            text: text.substring(0, 100) + (text.length > 100 ? '...' : ''), // Preview of classified text
            category: result.category,
            confidence: result.confidence,
            error: result.error,
            timestamp: new Date().toISOString(),
            serviceAvailable: activeClassifier.isServiceAvailable()
        });

    } catch (error) {
        logger.error('Classification API error:', error);
        res.status(500).json({
            error: 'Classification failed',
            details: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// Update email classification
router.patch('/:id/classify', async (req, res) => {
    try {
        const emailId = req.params.id;
        const { category, confidence } = req.body;

        if (!category) {
            return res.status(400).json({
                error: 'Missing category field in request body'
            });
        }

        // Get the current email
        const email = await esService.getEmailById(emailId);
        if (!email) {
            return res.status(404).json({ error: 'Email not found' });
        }

        // Update the email with new classification
        const source = (email._source as Record<string, any>) || {};
        source.aiCategory = category;
        source.aiConfidence = confidence || 0;

        // Use the indexEmail method which will update if exists
        await esService.indexEmail({
            id: emailId,
            ...source,
            date: new Date(source.date)
        } as any);

        res.json({
            success: true,
            emailId,
            category,
            confidence,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Update classification error:', error);
        res.status(500).json({
            error: 'Failed to update classification',
            details: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// ES module export
export default router;

// CommonJS export for compatibility
module.exports = router;
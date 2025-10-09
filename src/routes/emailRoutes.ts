import express from 'express';
import { ElasticsearchService } from '../Services/search/ElasticsearchService';
import { EmailClassificationService } from '../Services/ai/EmailClassificationService';
import logger from '../Services/utils/Logger';
import { DualIndexingAdapter } from '../Services/search/DualIndexingAdapter';

const router = express.Router();
const esService = new ElasticsearchService();
const classificationService = new EmailClassificationService();
const dualIndexingAdapter = new DualIndexingAdapter();

// Hybrid Search Endpoint
router.get('/search', async (req, res) => {
    try {
        const { q, type = 'hybrid', category } = req.query as Record<string, any>;

        if (!q) {
            return res.status(400).json({ error: 'Search query (q) is required' });
        }

        let results: any[] = [];

        if (type === 'keyword' || type === 'hybrid') {
            const keywordResults = await esService.search(q, undefined, undefined, category);
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
        logger.error('Hybrid search API error:', error);
        res.status(500).json({ error: 'Search failed' });
    }
});

// Get email by ID
router.get('/:id', async (req, res) => {
    try {
        const resp = await esService.getEmailById(req.params.id);
        // Fix: Handle potentially undefined _source with proper typing
        const source = resp._source as Record<string, any> || {};
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

        const result = await classificationService.classifyEmail(text);

        res.json({
            text: text.substring(0, 100) + (text.length > 100 ? '...' : ''), // Preview of classified text
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

// ES module export
export default router;

// CommonJS export for compatibility
module.exports = router;
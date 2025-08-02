import express from 'express';
import { ElasticsearchService } from '../Services/search/ElasticsearchService';
import { logger } from '../Services/utils/Logger';

const router = express.Router();
const esService = new ElasticsearchService();

// Search emails
router.get('/search', async (req, res) => {
    try {
        const { q, account, folder, category } = req.query as Record<string, any>;
        const result = await esService.search(
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

// ES module export
export default router;

// CommonJS export for compatibility
module.exports = router;
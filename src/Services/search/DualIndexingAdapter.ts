import { Email } from '../imap/Email';
import { EmailIndexingService, IndexingConfig } from './EmailIndexingService';
import { ElasticsearchService } from './ElasticsearchService';
import { logger } from '../utils/Logger';

/**
 * Migration adapter for gradual transition from ElasticsearchService to EmailIndexingService
 * 
 * This class provides a drop-in replacement for ElasticsearchService that adds
 * VectorDB capabilities while maintaining 100% backward compatibility.
 * 
 * Usage:
 * 1. Replace `new ElasticsearchService()` with `new DualIndexingAdapter()`
 * 2. Existing code continues to work unchanged
 * 3. New features (batch processing, vector search) become available
 * 4. Configure via environment variables or constructor options
 */
export class DualIndexingAdapter {
    private indexingService: EmailIndexingService | null = null;
    private fallbackService: ElasticsearchService;
    private isDualIndexing: boolean = false;

    constructor(config: Partial<IndexingConfig> = {}) {
        // Always create fallback service for compatibility
        this.fallbackService = new ElasticsearchService();

        // Check if VectorDB is actually enabled
        const vectorDBEnabled = process.env.ENABLE_VECTORDB?.toLowerCase() === 'true' || config.enableVectorDB === true;

        if (!vectorDBEnabled) {
            logger.info('DualIndexingAdapter: VectorDB disabled, using Elasticsearch-only mode');
            this.indexingService = null;
            this.isDualIndexing = false;
            return;
        }

        try {
            // Try to initialize dual indexing only if VectorDB is enabled
            const defaultConfig = {
                enableVectorDB: true,
                enableElasticsearch: true,
                enableTransactionSafety: process.env.TRANSACTION_SAFETY !== 'false',
                batchSize: parseInt(process.env.INDEXING_BATCH_SIZE || '20'),
                vectorDBEndpoint: process.env.VECTORDB_ENDPOINT || 'http://localhost:8001'
            };

            this.indexingService = new EmailIndexingService({ ...defaultConfig, ...config });
            this.isDualIndexing = true;

            logger.info('DualIndexingAdapter: Initialized with dual indexing support');
        } catch (error) {
            logger.warn('DualIndexingAdapter: Failed to initialize dual indexing, using Elasticsearch only:', error);
            this.indexingService = null;
            this.isDualIndexing = false;
        }
    }

    /**
     * BACKWARD COMPATIBLE: Index single email
     * Enhanced to use dual indexing if available
     */
    public async indexEmail(email: Email): Promise<void> {
        // If VectorDB is disabled, go straight to Elasticsearch-only
        if (!this.isDualIndexing || !this.indexingService) {
            return this.fallbackService.indexEmail(email);
        }

        try {
            const result = await this.indexingService.indexEmail(email);
            if (!result.success) {
                // Log the enhanced error info but don't throw for compatibility
                logger.warn(`Dual indexing partial failure for ${email.id}:`, result.errors);

                // If Elasticsearch succeeded, consider it successful for backward compatibility
                if (!result.elasticsearchSuccess) {
                    throw new Error(`Indexing failed: ${result.errors.join(', ')}`);
                }
            }
            return; // Success
        } catch (error) {
            logger.error('Dual indexing failed, falling back to Elasticsearch:', error);
            // Fall through to fallback
        }

        // Fallback to original Elasticsearch-only indexing
        return this.fallbackService.indexEmail(email);
    }

    /**
     * BACKWARD COMPATIBLE: Search functionality 
     */
    public async search(
        query: string,
        accountId?: string,
        folder?: string,
        category?: string
    ): Promise<{ total: number; emails: any[] }> {
        const activeService = this.isDualIndexing && this.indexingService
            ? this.indexingService
            : this.fallbackService;

        return activeService.search(query, accountId, folder, category);
    }

    /**
     * BACKWARD COMPATIBLE: Get email by ID
     */
    public async getEmailById(id: string): Promise<any> {
        const activeService = this.isDualIndexing && this.indexingService
            ? this.indexingService
            : this.fallbackService;

        return activeService.getEmailById(id);
    }

    /**
     * NEW FEATURE: Batch indexing (only available with dual indexing)
     */
    public async indexEmails(emails: Email[]): Promise<any> {
        if (!this.isDualIndexing || !this.indexingService) {
            // Fallback to sequential processing
            logger.info('Batch indexing not available, processing emails sequentially');
            const results = [];
            for (const email of emails) {
                try {
                    await this.indexEmail(email);
                    results.push({ success: true, emailId: email.id });
                } catch (error) {
                    results.push({
                        success: false,
                        emailId: email.id,
                        error: error instanceof Error ? error.message : 'Unknown error'
                    });
                }
            }
            return {
                totalProcessed: emails.length,
                totalSuccessful: results.filter(r => r.success).length,
                results
            };
        }

        return this.indexingService.indexEmails(emails);
    }

    /**
     * NEW FEATURE: Enhanced search with semantic capabilities
     * Falls back to regular search if vector search is not available
     */
    public async hybridSearch(
        query: string,
        options: {
            accountId?: string;
            folder?: string;
            category?: string;
            semanticWeight?: number;
            keywordWeight?: number;
            maxResults?: number;
        } = {}
    ): Promise<{ total: number; emails: any[]; searchType: 'hybrid' | 'keyword' }> {
        // If dual indexing is available, use hybrid search
        if (this.isDualIndexing && this.indexingService) {
            try {
                // This would integrate with the hybrid_search function we created earlier
                // For now, use regular search as placeholder
                const result = await this.search(query, options.accountId, options.folder, options.category);
                return { ...result, searchType: 'keyword' as const };
            } catch (error) {
                logger.warn('Hybrid search failed, falling back to keyword search:', error);
            }
        }

        // Fallback to keyword-only search
        const result = await this.search(query, options.accountId, options.folder, options.category);
        return { ...result, searchType: 'keyword' as const };
    }

    /**
     * Service status and capabilities
     */
    public getCapabilities() {
        return {
            dualIndexing: this.isDualIndexing,
            vectorSearch: this.isDualIndexing,
            batchProcessing: this.isDualIndexing,
            transactionSafety: this.isDualIndexing,
            hybridSearch: this.isDualIndexing,
            service: this.isDualIndexing ? 'EmailIndexingService' : 'ElasticsearchService'
        };
    }

    /**
     * Health check for all services
     */
    public async healthCheck(): Promise<{ elasticsearch: boolean; vectorDB: boolean; overall: boolean }> {
        if (this.isDualIndexing && this.indexingService) {
            try {
                return await this.indexingService.healthCheck();
            } catch (error) {
                logger.error('Dual indexing health check failed:', error);
            }
        }

        // Fallback health check
        try {
            await this.fallbackService.search('', undefined, undefined, undefined);
            return { elasticsearch: true, vectorDB: false, overall: true };
        } catch (error) {
            return { elasticsearch: false, vectorDB: false, overall: false };
        }
    }

    /**
     * Get statistics (enhanced if dual indexing is available)
     */
    public getStats() {
        if (this.isDualIndexing && this.indexingService) {
            return this.indexingService.getStats();
        }

        // Basic stats for Elasticsearch-only mode
        return {
            totalIndexed: 0, // Not tracked in original service
            totalErrors: 0,
            elasticsearchErrors: 0,
            vectorDBErrors: 0,
            lastIndexTime: new Date(),
            config: {
                enableVectorDB: false,
                enableElasticsearch: true,
                enableTransactionSafety: false,
                batchSize: 1
            },
            vectorDBAvailable: false
        };
    }

    /**
     * Progressive enhancement: gradually enable dual indexing
     */
    public async enableDualIndexing(config: Partial<IndexingConfig> = {}): Promise<boolean> {
        if (this.isDualIndexing) {
            logger.info('Dual indexing already enabled');
            return true;
        }

        try {
            const defaultConfig = {
                enableVectorDB: true,
                enableElasticsearch: true,
                enableTransactionSafety: true,
                batchSize: 20,
                vectorDBEndpoint: process.env.VECTORDB_ENDPOINT || 'http://localhost:8001'
            };

            this.indexingService = new EmailIndexingService({ ...defaultConfig, ...config });

            // Test the service
            const health = await this.indexingService.healthCheck();
            if (health.overall) {
                this.isDualIndexing = true;
                logger.info('Dual indexing enabled successfully');
                return true;
            } else {
                throw new Error(`Health check failed: ${JSON.stringify(health)}`);
            }
        } catch (error) {
            logger.error('Failed to enable dual indexing:', error);
            this.indexingService = null;
            return false;
        }
    }

    /**
     * Disable dual indexing and revert to Elasticsearch-only
     */
    public disableDualIndexing(): void {
        if (this.isDualIndexing) {
            this.indexingService = null;
            this.isDualIndexing = false;
            logger.info('Dual indexing disabled, reverted to Elasticsearch-only');
        }
    }
}

// Export for CommonJS compatibility - removed to prevent circular dependency
// module.exports = DualIndexingAdapter;
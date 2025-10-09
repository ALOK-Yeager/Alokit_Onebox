import { Email } from '../imap/Email';
import { EnhancedElasticsearchService } from './EnhancedElasticsearchService';
import { logger } from '../utils/Logger';

// Interface for Python VectorDB service
interface VectorDBService {
    add_email(email_id: string, content: string): Promise<boolean>;
    add_emails(emails: Array<{ email_id: string, content: string }>): Promise<boolean>;
    search(query: string, n_results?: number): Promise<any[]>;
    delete_email(email_id: string): Promise<boolean>;
    delete_emails(email_ids: string[]): Promise<boolean>;
}

// Configuration for indexing behavior
export interface IndexingConfig {
    enableVectorDB: boolean;
    enableElasticsearch: boolean;
    enableTransactionSafety: boolean;
    batchSize: number;
    maxRetries: number;
    retryDelayMs: number;
    vectorDBEndpoint?: string;
    progressCallback?: (progress: IndexingProgress) => void;
}

// Progress tracking for batch operations
export interface IndexingProgress {
    processed: number;
    total: number;
    successful: number;
    failed: number;
    errors: string[];
    startTime: Date;
    estimatedTimeRemaining?: number;
}

// Result object for indexing operations
export interface IndexingResult {
    success: boolean;
    elasticsearchSuccess: boolean;
    vectorDBSuccess: boolean;
    errors: string[];
    emailId: string;
    processingTimeMs: number;
}

// Result object for batch operations
export interface BatchIndexingResult {
    totalProcessed: number;
    totalSuccessful: number;
    totalFailed: number;
    elasticsearchSuccessful: number;
    vectorDBSuccessful: number;
    results: IndexingResult[];
    totalProcessingTimeMs: number;
    errors: string[];
}

/**
 * EmailIndexingService coordinates dual indexing between Elasticsearch and VectorDB
 * with transaction safety, batch processing, and comprehensive error handling.
 * 
 * Features:
 * - Parallel indexing to Elasticsearch + VectorDB
 * - Transaction safety (if one fails, both rollback)
 * - Batch processing for efficiency
 * - Progress tracking and error logging
 * - Backward compatibility with existing ElasticsearchService
 * - Configurable retry logic and fallback behavior
 */
export class EmailIndexingService {
    private elasticsearchService: EnhancedElasticsearchService;
    private vectorDBService: VectorDBService | null = null;
    private config: IndexingConfig;
    private stats = {
        totalIndexed: 0,
        totalErrors: 0,
        elasticsearchErrors: 0,
        vectorDBErrors: 0,
        rollbacks: 0,
        lastIndexTime: new Date()
    };

    constructor(config: Partial<IndexingConfig> = {}) {
        this.elasticsearchService = new EnhancedElasticsearchService();

        // Default configuration
        this.config = {
            enableVectorDB: true,
            enableElasticsearch: true,
            enableTransactionSafety: true,
            batchSize: 20,
            maxRetries: 3,
            retryDelayMs: 1000,
            vectorDBEndpoint: process.env.VECTORDB_ENDPOINT || 'http://localhost:8001',
            ...config
        };

        // Initialize VectorDB service if enabled
        if (this.config.enableVectorDB) {
            this.initializeVectorDB();
        }

        logger.info('EmailIndexingService initialized', {
            elasticsearch: this.config.enableElasticsearch,
            vectorDB: this.config.enableVectorDB,
            transactionSafety: this.config.enableTransactionSafety,
            batchSize: this.config.batchSize
        });
    }

    /**
     * Initialize connection to Python VectorDB service
     */
    private async initializeVectorDB(): Promise<void> {
        try {
            // Create a simple HTTP client for Python VectorDB service
            this.vectorDBService = {
                add_email: async (email_id: string, content: string): Promise<boolean> => {
                    try {
                        const response = await fetch(`${this.config.vectorDBEndpoint}/add_email`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email_id, content }),
                            signal: AbortSignal.timeout(10000) // 10s timeout
                        });
                        return response.ok;
                    } catch (error) {
                        logger.error('VectorDB add_email error:', error);
                        return false;
                    }
                },

                add_emails: async (emails: Array<{ email_id: string, content: string }>): Promise<boolean> => {
                    try {
                        const response = await fetch(`${this.config.vectorDBEndpoint}/add_emails`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ emails }),
                            signal: AbortSignal.timeout(30000) // 30s timeout for batch
                        });
                        return response.ok;
                    } catch (error) {
                        logger.error('VectorDB add_emails error:', error);
                        return false;
                    }
                },

                search: async (query: string, n_results: number = 5): Promise<any[]> => {
                    try {
                        const response = await fetch(`${this.config.vectorDBEndpoint}/search?q=${encodeURIComponent(query)}&n_results=${n_results}`, {
                            signal: AbortSignal.timeout(10000)
                        });
                        if (response.ok) {
                            const data = await response.json() as { results?: any[] };
                            return data.results || [];
                        }
                        return [];
                    } catch (error) {
                        logger.error('VectorDB search error:', error);
                        return [];
                    }
                },

                delete_email: async (email_id: string): Promise<boolean> => {
                    try {
                        const response = await fetch(`${this.config.vectorDBEndpoint}/delete_email`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email_id }),
                            signal: AbortSignal.timeout(10000)
                        });
                        return response.ok;
                    } catch (error) {
                        logger.error('VectorDB delete_email error:', error);
                        return false;
                    }
                },

                delete_emails: async (email_ids: string[]): Promise<boolean> => {
                    try {
                        const response = await fetch(`${this.config.vectorDBEndpoint}/delete_emails`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email_ids }),
                            signal: AbortSignal.timeout(20000)
                        });
                        return response.ok;
                    } catch (error) {
                        logger.error('VectorDB delete_emails error:', error);
                        return false;
                    }
                }
            };

            logger.info('VectorDB service initialized', { endpoint: this.config.vectorDBEndpoint });
        } catch (error) {
            logger.error('Failed to initialize VectorDB service:', error);
            this.vectorDBService = null;
        }
    }

    /**
     * Index a single email to both Elasticsearch and VectorDB
     * 
     * @param email Email object to index
     * @returns IndexingResult with detailed success/failure information
     */
    public async indexEmail(email: Email): Promise<IndexingResult> {
        const startTime = Date.now();
        const result: IndexingResult = {
            success: false,
            elasticsearchSuccess: false,
            vectorDBSuccess: false,
            errors: [],
            emailId: email.id,
            processingTimeMs: 0
        };

        try {
            logger.debug(`Starting dual indexing for email ${email.id}`);

            // Prepare content for vector indexing (subject + body)
            const vectorContent = `${email.subject || ''}\n\n${email.body || ''}`.trim();

            let elasticsearchPromise: Promise<boolean> | null = null;
            let vectorDBPromise: Promise<boolean> | null = null;

            // Start both indexing operations in parallel
            if (this.config.enableElasticsearch) {
                elasticsearchPromise = this.indexToElasticsearch(email);
            }

            if (this.config.enableVectorDB && this.vectorDBService && vectorContent.length > 10) {
                vectorDBPromise = this.indexToVectorDB(email.id, vectorContent);
            }

            // Wait for both operations to complete
            const results = await Promise.allSettled([
                elasticsearchPromise,
                vectorDBPromise
            ].filter(p => p !== null) as Promise<boolean>[]);

            // Process results
            if (elasticsearchPromise) {
                result.elasticsearchSuccess = results[0]?.status === 'fulfilled' && results[0].value === true;
                if (!result.elasticsearchSuccess) {
                    const error = results[0]?.status === 'rejected' ? results[0].reason : 'Elasticsearch indexing failed';
                    result.errors.push(`Elasticsearch: ${error}`);
                    this.stats.elasticsearchErrors++;
                }
            } else {
                result.elasticsearchSuccess = true; // Not enabled, so considered successful
            }

            if (vectorDBPromise) {
                const vectorResult = results[elasticsearchPromise ? 1 : 0];
                result.vectorDBSuccess = vectorResult?.status === 'fulfilled' && vectorResult.value === true;
                if (!result.vectorDBSuccess) {
                    const error = vectorResult?.status === 'rejected' ? vectorResult.reason : 'VectorDB indexing failed';
                    result.errors.push(`VectorDB: ${error}`);
                    this.stats.vectorDBErrors++;
                }
            } else {
                result.vectorDBSuccess = true; // Not enabled or no content, so considered successful
            }

            // Apply transaction safety if enabled
            if (this.config.enableTransactionSafety) {
                result.success = result.elasticsearchSuccess && result.vectorDBSuccess;

                // If transaction failed, attempt rollback
                if (!result.success) {
                    await this.rollbackIndexing(email.id, result.elasticsearchSuccess, result.vectorDBSuccess);
                    result.errors.push('Transaction rolled back due to partial failure');
                }
            } else {
                // Without transaction safety, success if at least one indexing succeeded
                result.success = result.elasticsearchSuccess || result.vectorDBSuccess;
            }

            // Update stats
            if (result.success) {
                this.stats.totalIndexed++;
                this.stats.lastIndexTime = new Date();
            } else {
                this.stats.totalErrors++;
            }

            result.processingTimeMs = Date.now() - startTime;

            logger.info(`Email ${email.id} indexing completed`, {
                success: result.success,
                elasticsearch: result.elasticsearchSuccess,
                vectorDB: result.vectorDBSuccess,
                processingTimeMs: result.processingTimeMs,
                errors: result.errors.length
            });

            return result;

        } catch (error) {
            result.processingTimeMs = Date.now() - startTime;
            result.errors.push(`Unexpected error: ${error}`);
            this.stats.totalErrors++;

            logger.error(`Failed to index email ${email.id}:`, error);
            return result;
        }
    }

    /**
     * Index multiple emails in batches for efficiency
     */
    public async indexEmails(emails: Email[]): Promise<BatchIndexingResult> {
        const startTime = Date.now();
        const progress: IndexingProgress = {
            processed: 0,
            total: emails.length,
            successful: 0,
            failed: 0,
            errors: [],
            startTime: new Date()
        };

        const batchResult: BatchIndexingResult = {
            totalProcessed: 0,
            totalSuccessful: 0,
            totalFailed: 0,
            elasticsearchSuccessful: 0,
            vectorDBSuccessful: 0,
            results: [],
            totalProcessingTimeMs: 0,
            errors: []
        };

        logger.info(`Starting batch indexing of ${emails.length} emails`, {
            batchSize: this.config.batchSize,
            transactionSafety: this.config.enableTransactionSafety
        });

        try {
            // Process emails in batches
            for (let i = 0; i < emails.length; i += this.config.batchSize) {
                const batch = emails.slice(i, i + this.config.batchSize);
                logger.debug(`Processing batch ${Math.floor(i / this.config.batchSize) + 1}/${Math.ceil(emails.length / this.config.batchSize)}`);

                // Process batch in parallel with limited concurrency
                const batchPromises = batch.map(email => this.indexEmail(email));
                const batchResults = await Promise.all(batchPromises);

                // Aggregate results
                for (const result of batchResults) {
                    batchResult.results.push(result);
                    batchResult.totalProcessed++;

                    if (result.success) {
                        batchResult.totalSuccessful++;
                    } else {
                        batchResult.totalFailed++;
                        batchResult.errors.push(...result.errors);
                    }

                    if (result.elasticsearchSuccess) batchResult.elasticsearchSuccessful++;
                    if (result.vectorDBSuccess) batchResult.vectorDBSuccessful++;

                    progress.processed++;
                    if (result.success) progress.successful++;
                    else progress.failed++;
                }

                // Update progress and call callback if provided
                const elapsed = Date.now() - startTime;
                const rate = progress.processed / (elapsed / 1000);
                progress.estimatedTimeRemaining = (progress.total - progress.processed) / rate;

                if (this.config.progressCallback) {
                    this.config.progressCallback(progress);
                }

                // Brief pause between batches to avoid overwhelming services
                if (i + this.config.batchSize < emails.length) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
            }

            batchResult.totalProcessingTimeMs = Date.now() - startTime;

            logger.info(`Batch indexing completed`, {
                totalProcessed: batchResult.totalProcessed,
                successful: batchResult.totalSuccessful,
                failed: batchResult.totalFailed,
                elasticsearchSuccessful: batchResult.elasticsearchSuccessful,
                vectorDBSuccessful: batchResult.vectorDBSuccessful,
                totalTimeMs: batchResult.totalProcessingTimeMs,
                averageTimePerEmail: batchResult.totalProcessingTimeMs / batchResult.totalProcessed
            });

            return batchResult;

        } catch (error) {
            logger.error('Batch indexing failed:', error);
            batchResult.errors.push(`Batch processing error: ${error}`);
            batchResult.totalProcessingTimeMs = Date.now() - startTime;
            return batchResult;
        }
    }

    /**
     * Index email to Elasticsearch with retry logic
     */
    private async indexToElasticsearch(email: Email): Promise<boolean> {
        for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
            try {
                await this.elasticsearchService.indexEmail(email);
                return true;
            } catch (error) {
                logger.warn(`Elasticsearch indexing attempt ${attempt}/${this.config.maxRetries} failed:`, error);

                if (attempt < this.config.maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, this.config.retryDelayMs * attempt));
                } else {
                    throw error;
                }
            }
        }
        return false;
    }

    /**
     * Index email to VectorDB with retry logic
     */
    private async indexToVectorDB(emailId: string, content: string): Promise<boolean> {
        if (!this.vectorDBService) return false;

        for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
            try {
                const success = await this.vectorDBService.add_email(emailId, content);
                if (success) return true;

                throw new Error('VectorDB returned false');
            } catch (error) {
                logger.warn(`VectorDB indexing attempt ${attempt}/${this.config.maxRetries} failed:`, error);

                if (attempt < this.config.maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, this.config.retryDelayMs * attempt));
                } else {
                    throw error;
                }
            }
        }
        return false;
    }

    /**
     * Rollback indexing in case of transaction failure
     */
    private async rollbackIndexing(emailId: string, elasticsearchSuccess: boolean, vectorDBSuccess: boolean): Promise<void> {
        logger.warn(`Rolling back transaction for email ${emailId}`);
        const rollbackPromises: Promise<any>[] = [];
        let rollbackErrors: string[] = [];

        // Rollback Elasticsearch if it was successful
        if (elasticsearchSuccess) {
            rollbackPromises.push(
                this.elasticsearchService.deleteEmail(emailId)
                    .then(success => {
                        if (!success) {
                            rollbackErrors.push(`Failed to rollback Elasticsearch for ${emailId}`);
                        } else {
                            logger.debug(`Successfully rolled back Elasticsearch for ${emailId}`);
                        }
                    })
                    .catch(error => {
                        rollbackErrors.push(`Elasticsearch rollback error for ${emailId}: ${error}`);
                    })
            );
        }

        // Rollback VectorDB if it was successful
        if (vectorDBSuccess && this.vectorDBService) {
            rollbackPromises.push(
                this.vectorDBService.delete_email(emailId)
                    .then(success => {
                        if (!success) {
                            rollbackErrors.push(`Failed to rollback VectorDB for ${emailId}`);
                        } else {
                            logger.debug(`Successfully rolled back VectorDB for ${emailId}`);
                        }
                    })
                    .catch(error => {
                        rollbackErrors.push(`VectorDB rollback error for ${emailId}: ${error}`);
                    })
            );
        }

        // Wait for all rollback operations to complete
        await Promise.all(rollbackPromises);

        if (rollbackErrors.length > 0) {
            logger.error(`Rollback completed with errors: ${rollbackErrors.join(', ')}`);
        } else {
            logger.info(`Rollback completed successfully for email ${emailId}`);
        }

        this.stats.rollbacks++;
    }

    /**
     * Rollback batch indexing in case of transaction failure
     */
    private async rollbackBatchIndexing(
        successfulEmails: { emailId: string; elasticsearchSuccess: boolean; vectorDBSuccess: boolean }[]
    ): Promise<void> {
        if (successfulEmails.length === 0) return;

        logger.warn(`Rolling back batch transaction for ${successfulEmails.length} emails`);

        const elasticsearchRollbacks: string[] = [];
        const vectorDBRollbacks: string[] = [];

        // Collect emails that need rollback
        for (const email of successfulEmails) {
            if (email.elasticsearchSuccess) {
                elasticsearchRollbacks.push(email.emailId);
            }
            if (email.vectorDBSuccess) {
                vectorDBRollbacks.push(email.emailId);
            }
        }

        const rollbackPromises: Promise<void>[] = [];

        // Batch rollback Elasticsearch
        if (elasticsearchRollbacks.length > 0) {
            rollbackPromises.push(
                this.elasticsearchService.deleteEmails(elasticsearchRollbacks)
                    .then(result => {
                        if (result.failed > 0) {
                            logger.error(`Elasticsearch batch rollback failed for ${result.failed} emails: ${result.errors.join(', ')}`);
                        } else {
                            logger.info(`Successfully rolled back ${result.successful} emails from Elasticsearch`);
                        }
                    })
                    .catch(error => {
                        logger.error('Elasticsearch batch rollback error:', error);
                    })
            );
        }

        // Batch rollback VectorDB
        if (vectorDBRollbacks.length > 0 && this.vectorDBService) {
            rollbackPromises.push(
                this.vectorDBService.delete_emails(vectorDBRollbacks)
                    .then(success => {
                        if (!success) {
                            logger.error(`VectorDB batch rollback failed for ${vectorDBRollbacks.length} emails`);
                        } else {
                            logger.info(`Successfully rolled back ${vectorDBRollbacks.length} emails from VectorDB`);
                        }
                    })
                    .catch(error => {
                        logger.error('VectorDB batch rollback error:', error);
                    })
            );
        }

        await Promise.all(rollbackPromises);

        this.stats.rollbacks += successfulEmails.length;
        logger.info(`Batch rollback completed for ${successfulEmails.length} emails`);
    }

    /**
     * Backward compatibility: delegate to ElasticsearchService for existing code
     */
    public async search(query: string, accountId?: string, folder?: string, category?: string): Promise<{ total: number; emails: any[] }> {
        return this.elasticsearchService.search(query, accountId, folder, category);
    }

    /**
     * Backward compatibility: delegate to ElasticsearchService
     */
    public async getEmailById(id: string): Promise<any> {
        return this.elasticsearchService.getEmailById(id);
    }

    /**
     * Get service statistics
     */
    public getStats() {
        return {
            ...this.stats,
            config: {
                enableVectorDB: this.config.enableVectorDB,
                enableElasticsearch: this.config.enableElasticsearch,
                enableTransactionSafety: this.config.enableTransactionSafety,
                batchSize: this.config.batchSize
            },
            vectorDBAvailable: this.vectorDBService !== null
        };
    }

    /**
     * Test both services connectivity
     */
    public async healthCheck(): Promise<{ elasticsearch: boolean; vectorDB: boolean; overall: boolean }> {
        const health = {
            elasticsearch: false,
            vectorDB: false,
            overall: false
        };

        try {
            // Test Elasticsearch
            if (this.config.enableElasticsearch) {
                await this.elasticsearchService.search('', undefined, undefined, undefined);
                health.elasticsearch = true;
            }
        } catch (error) {
            logger.warn('Elasticsearch health check failed:', error);
        }

        try {
            // Test VectorDB
            if (this.config.enableVectorDB && this.vectorDBService) {
                await this.vectorDBService.search('test', 1);
                health.vectorDB = true;
            }
        } catch (error) {
            logger.warn('VectorDB health check failed:', error);
        }

        health.overall = (!this.config.enableElasticsearch || health.elasticsearch) &&
            (!this.config.enableVectorDB || health.vectorDB);

        return health;
    }
}

// Export for CommonJS compatibility - removed to prevent circular dependency
// module.exports = EmailIndexingService;
import { Email } from '../imap/Email';
import { ElasticsearchService } from './ElasticsearchService';
import logger from '../utils/Logger';

/**
 * Enhanced ElasticsearchService with rollback capabilities
 * Extends the original service with delete operations for transaction safety
 */
export class EnhancedElasticsearchService extends ElasticsearchService {
    /**
     * Delete an email from the index (for rollback operations)
     */
    public async deleteEmail(emailId: string): Promise<boolean> {
        try {
            const response = await (this as any).client.delete({
                index: (this as any).indexName,
                id: emailId,
                refresh: true
            });

            logger.debug(`Deleted email ${emailId} from Elasticsearch`);
            return response.result === 'deleted';
        } catch (error) {
            // If document doesn't exist, consider it successfully deleted
            if ((error as any)?.meta?.statusCode === 404) {
                logger.debug(`Email ${emailId} not found in Elasticsearch (already deleted)`);
                return true;
            }

            logger.error(`Failed to delete email ${emailId} from Elasticsearch:`, error);
            return false;
        }
    }

    /**
     * Check if an email exists in the index
     */
    public async emailExists(emailId: string): Promise<boolean> {
        try {
            const response = await (this as any).client.exists({
                index: (this as any).indexName,
                id: emailId
            });
            return response;
        } catch (error) {
            logger.error(`Failed to check if email ${emailId} exists:`, error);
            return false;
        }
    }

    /**
     * Bulk delete emails (for batch rollback)
     */
    public async deleteEmails(emailIds: string[]): Promise<{ successful: number; failed: number; errors: string[] }> {
        if (emailIds.length === 0) {
            return { successful: 0, failed: 0, errors: [] };
        }

        try {
            const body = emailIds.flatMap(id => [
                { delete: { _index: (this as any).indexName, _id: id } }
            ]);

            const response = await (this as any).client.bulk({
                body,
                refresh: true
            });

            let successful = 0;
            let failed = 0;
            const errors: string[] = [];

            if (response.items) {
                for (const item of response.items) {
                    if (item.delete) {
                        if (item.delete.status === 200 || item.delete.status === 404) {
                            successful++;
                        } else {
                            failed++;
                            errors.push(`Failed to delete ${item.delete._id}: ${item.delete.error?.reason || 'Unknown error'}`);
                        }
                    }
                }
            }

            logger.info(`Bulk delete completed: ${successful} successful, ${failed} failed`);
            return { successful, failed, errors };

        } catch (error) {
            logger.error('Bulk delete operation failed:', error);
            return {
                successful: 0,
                failed: emailIds.length,
                errors: [`Bulk delete failed: ${error instanceof Error ? error.message : 'Unknown error'}`]
            };
        }
    }

    /**
     * Create a backup of email data before modification (for advanced rollback)
     */
    public async backupEmail(emailId: string): Promise<any | null> {
        try {
            const response = await this.getEmailById(emailId);
            if (!response) {
                logger.debug(`No existing document to back up for ${emailId}`);
                return null;
            }
            return response._source;
        } catch (error) {
            logger.error(`Failed to backup email ${emailId}:`, error);
            return null;
        }
    }

    /**
     * Restore email from backup data
     */
    public async restoreEmail(emailId: string, backupData: any): Promise<boolean> {
        try {
            await (this as any).client.index({
                index: (this as any).indexName,
                id: emailId,
                document: backupData,
                refresh: true
            });

            logger.debug(`Restored email ${emailId} from backup`);
            return true;
        } catch (error) {
            logger.error(`Failed to restore email ${emailId}:`, error);
            return false;
        }
    }
}

// Export for CommonJS compatibility - removed to prevent circular dependency
// module.exports = EnhancedElasticsearchService;
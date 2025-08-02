import { Client, ClientOptions } from '@elastic/elasticsearch';
import { Email } from '../imap/Email';
import { logger } from '../utils/Logger';

declare var module: any;

export class ElasticsearchService {
    private client: Client;
    private readonly indexName = 'emails';

    constructor() {
        const clientOptions: ClientOptions = {
            node: process.env.ELASTICSEARCH_NODE || 'http://localhost:9200',
            tls: {
                rejectUnauthorized: false
            }
        };

        this.client = new Client(clientOptions);
        this.initIndex().catch(console.error);
    }

    private async initIndex(): Promise<void> {
        try {
            const exists = await this.client.indices.exists({ index: this.indexName });

            if (!exists) {
                await this.client.indices.create({
                    index: this.indexName,
                    mappings: {
                        dynamic: 'strict',
                        properties: {
                            id: { type: 'keyword' },
                            uid: { type: 'long' },
                            seqno: { type: 'long' },
                            accountId: { type: 'keyword' },
                            folder: { type: 'keyword' },
                            subject: {
                                type: 'text',
                                fields: {
                                    keyword: { type: 'keyword' }
                                }
                            },
                            from: { type: 'keyword' },
                            to: { type: 'keyword' },
                            cc: { type: 'keyword' },
                            bcc: { type: 'keyword' },
                            date: { type: 'date' },
                            body: { type: 'text' },
                            html: { type: 'text' },
                            aiCategory: { type: 'keyword' },
                            aiConfidence: { type: 'float' },
                            generatedReply: { type: 'text' },
                            attachments: {
                                type: 'nested',
                                properties: {
                                    filename: { type: 'text' },
                                    contentType: { type: 'keyword' },
                                    size: { type: 'long' }
                                }
                            }
                        }
                    }
                });
                console.log('Elasticsearch index created with proper mappings');
            }
        } catch (error) {
            console.error('Error initializing Elasticsearch index:', error);
            throw error;
        }
    }

    public async indexEmail(email: Email): Promise<void> {
        try {
            const emailForIndex = {
                id: email.id,
                uid: email.uid,
                seqno: email.seqno,
                accountId: email.accountId,
                folder: email.folder,
                subject: email.subject,
                from: email.from,
                to: email.to,
                cc: email.cc,
                bcc: email.bcc,
                date: new Date(email.date).toISOString(),
                body: email.body,
                html: email.html,
                aiCategory: email.aiCategory,
                aiConfidence: email.aiConfidence,
                generatedReply: email.generatedReply,
                attachments: email.attachments?.map(a => ({
                    filename: a.filename,
                    contentType: a.contentType,
                    size: a.size
                }))
            };

            await this.client.index({
                index: this.indexName,
                id: email.id,
                document: emailForIndex,
                refresh: true
            });

            console.log(`Indexed email ${email.id} successfully`);
        } catch (error) {
            console.error('Error indexing email:', error);
            throw error;
        }
    }

    public async search(
        query: string,
        accountId?: string,
        folder?: string,
        category?: string
    ): Promise<{ total: number; emails: any[] }> {
        try {
            const body: any = {
                query: {
                    bool: {
                        must: [],
                        filter: []
                    }
                },
                sort: [{ date: 'desc' }]
            };

            // Add text search if query provided
            if (query && query.trim() !== '') {
                body.query.bool.must.push({
                    multi_match: {
                        query,
                        fields: ['subject^3', 'body', 'from.name'],
                        type: 'best_fields'
                    }
                });
            }

            // Add filters if provided
            if (accountId) {
                body.query.bool.filter.push({ term: { accountId } });
            }

            if (folder) {
                body.query.bool.filter.push({ term: { folder } });
            }

            if (category) {
                body.query.bool.filter.push({ term: { aiCategory: category } });
            }

            const result = await this.client.search({
                index: this.indexName,
                body,
                size: 50
            });

            const total = typeof result.hits.total === 'number'
                ? result.hits.total
                : (result.hits.total?.value ?? 0);
            return {
                total,
                emails: result.hits.hits.map(hit => ({
                    id: hit._id,
                    ...(hit._source as object)
                }))
            };
        } catch (error) {
            console.error('Search error:', error);
            throw error;
        }
    }

    public async getEmailById(id: string) {
        return this.client.get({ index: this.indexName, id });
    }

    // Helper methods for email address parsing
    private extractEmail(address: string): string {
        const match = address.match(/<([^>]+)>/);
        return match?.[1] ?? address;
    }

    private extractName(address: string | undefined): string {
        const safeAddress = address ?? '';
        const match = safeAddress.match(/"?(.*?)"?\s*</);
        if (match && match[1]) {
            return match[1];
        }
        const parts = safeAddress.split('<');
        return parts.length > 0 ? parts[0]?.trim() ?? '' : '';
    }

    private parseAddressList(addresses: string | string[] | undefined): string[] {
        if (!addresses) return [];
        const list = Array.isArray(addresses) ? addresses : [addresses];
        return list.map(addr => this.extractEmail(addr));
    }
}

// Export for CommonJS compatibility
module.exports = ElasticsearchService;
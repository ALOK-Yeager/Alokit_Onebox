const Imap = require('imap');
const { logger } = require('../utils/Logger');
const { EmailParser } = require('./EmailParser');

class Sync {
    private lastUid = 0;
    private readonly BATCH_SIZE = 50;

    constructor(
        private imap: any,
        private accountConfig: any,
        private emailParser: any,
        private onEmailReceived: (email: any) => void,
        private onEmailIndexed: (emailId: string) => void
    ) { }

    public async fetchHistoricalEmails(): Promise<void> {
        // Calculate 30 days ago (assignment requirement)
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        logger.info(`Fetching historical emails from ${thirtyDaysAgo.toISOString()} for ${this.accountConfig.email}`);

        return new Promise((resolve, reject) => {
            // Search criteria for last 30 days
            const searchCriteria = [
                'SINCE', thirtyDaysAgo
            ];

            this.imap.search(searchCriteria, async (err: Error | null, results: number[]) => {
                if (err) {
                    logger.error(`Search error for historical emails for ${this.accountConfig.email}:`, err);
                    return reject(err);
                }

                if (results.length === 0) {
                    logger.info(`No historical emails found for ${this.accountConfig.email}`);
                    return resolve();
                }

                logger.info(`Found ${results.length} historical emails for ${this.accountConfig.email}`);

                // Process in batches to avoid memory issues
                let processed = 0;

                const processNextBatch = async () => {
                    if (processed >= results.length) {
                        logger.info(`Completed historical sync for ${this.accountConfig.email}`);
                        return resolve();
                    }

                    const batch = results.slice(processed, processed + this.BATCH_SIZE);
                    processed += batch.length;

                    try {
                        await this.processEmailBatch(batch);
                        setImmediate(processNextBatch);
                    } catch (err) {
                        logger.error(`Batch processing error for ${this.accountConfig.email}:`, err);
                        resolve(); // Continue with next batch
                    }
                };

                processNextBatch();
            });
        });
    }

    private async processEmailBatch(uids: number[]): Promise<void> {
        return new Promise((resolve, reject) => {
            const fetchOptions = {
                bodies: ['HEADER', 'TEXT'],
                markSeen: false,
                struct: true
            };

            const f = this.imap.fetch(uids, fetchOptions);

            f.on('message', async (msg: any, seqno: number) => {
                try {
                    const email = await this.emailParser.parseMessage(msg, seqno, this.accountConfig.id);
                    this.onEmailReceived(email);

                    // Update lastUid to prevent reprocessing
                    if (email.uid > this.lastUid) {
                        this.lastUid = email.uid;
                    }
                } catch (err) {
                    logger.error(`Email parsing error for ${this.accountConfig.email}:`, err);
                }
            });

            f.once('error', (err: Error) => {
                logger.error(`Fetch error for batch in ${this.accountConfig.email}:`, err);
                reject(err);
            });

            f.once('end', () => {
                logger.debug(`Processed batch of ${uids.length} emails for ${this.accountConfig.email}`);
                resolve();
            });
        });
    }

    public async fetchNewEmails(numNewMsgs: number): Promise<void> {
        try {
            // Search for unseen messages
            const searchCriteria = ['UNSEEN'];
            const fetchOptions = {
                bodies: ['HEADER', 'TEXT'],
                markSeen: false
            };

            return new Promise((resolve, reject) => {
                this.imap.search(searchCriteria, async (err: Error | null, results: number[]) => {
                    if (err) {
                        logger.error(`Search error for new emails for ${this.accountConfig.email}:`, err);
                        return reject(err);
                    }

                    if (results.length === 0) {
                        logger.info(`No new unseen emails found for ${this.accountConfig.email}`);
                        return resolve();
                    }

                    // Process only the most recent messages
                    const newEmails = results.slice(-numNewMsgs);
                    logger.info(`Processing ${newEmails.length} new email(s) for ${this.accountConfig.email}`);

                    try {
                        await this.processEmailBatch(newEmails);
                        resolve();
                    } catch (err) {
                        reject(err);
                    }
                });
            });
        } catch (err) {
            logger.error(`Error fetching new emails for ${this.accountConfig.email}:`, err);
            throw err;
        }
    }
}

module.exports = { Sync };
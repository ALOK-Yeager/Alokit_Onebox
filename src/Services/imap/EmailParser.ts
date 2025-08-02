const Imap = require('imap');
const { simpleParser } = require('mailparser');
const { logger } = require('../utils/Logger');

class EmailParser {
    public async parseMessage(
        msg: any,
        seqno: number,
        accountId: string
    ): Promise<any> {
        return new Promise((resolve, reject) => {
            let emailData: any = {
                uid: 0,
                seqno,
                accountId,
                folder: 'INBOX',
                attachments: [],
                headers: {}
            };
            const chunks: Buffer[] = [];
            let headers: any = {};

            msg.on('body', (stream: any, info: any) => {
                let buffer = '';
                stream.on('data', (chunk: any) => {
                    chunks.push(chunk);
                    if (info.which === 'HEADER') {
                        buffer += chunk.toString('utf8');
                    }
                });
                stream.once('end', () => {
                    if (info.which === 'HEADER') {
                        headers = Imap.parseHeader(buffer);
                    }
                });
            });

            msg.once('attributes', (attrs: any) => {
                emailData.uid = attrs.uid;
            });

            msg.once('end', async () => {
                try {
                    const fullMessage = Buffer.concat(chunks);
                    const parsed = await simpleParser(fullMessage);

                    emailData.from = parsed.from?.text || '';
                    emailData.to = parsed.to?.text || '';
                    emailData.cc = parsed.cc?.text;
                    emailData.bcc = parsed.bcc?.text;
                    emailData.subject = parsed.subject || '(no subject)';
                    emailData.date = parsed.date || new Date();
                    emailData.body = parsed.text || '';
                    emailData.headers = headers;

                    emailData.attachments = (parsed.attachments || []).map((a: any) => ({
                        filename: a.filename || `attachment-${Date.now()}`,
                        contentType: a.contentType || 'application/octet-stream',
                        size: a.size,
                        content: a.content as Buffer
                    }));

                    // Generate a unique ID for the email
                    const id = this.generateEmailId(
                        emailData.uid?.toString() || '',
                        accountId,
                        emailData.date?.toISOString() || ''
                    );

                    const completeEmail: any = {
                        id,
                        uid: emailData.uid || 0,
                        seqno: emailData.seqno || 0,
                        accountId: emailData.accountId || '',
                        folder: emailData.folder || 'INBOX',
                        subject: emailData.subject || '',
                        from: emailData.from || '',
                        to: emailData.to || '',
                        cc: emailData.cc,
                        bcc: emailData.bcc,
                        date: emailData.date || new Date(),
                        body: emailData.body || '',
                        html: emailData.html,
                        attachments: emailData.attachments || [],
                        headers: emailData.headers || {}
                    };

                    resolve(completeEmail);
                } catch (err) {
                    logger.error('Email parsing error:', err);
                    reject(err);
                }
            });
        });
    }

    private extractHeaderField(header: any, field: string): string {
        return Array.isArray(header[field]) ? header[field][0] : header[field] || '';
    }

    private generateEmailId(uid: string, accountId: string, date: string): string {
        // Create a deterministic but unique ID
        return `email-${accountId}-${uid}-${date.replace(/[^a-zA-Z0-9]/g, '')}`;
    }
}

module.exports = { EmailParser };

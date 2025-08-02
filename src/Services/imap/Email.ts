interface Email {
    id: string;
    uid: number;
    seqno: number;
    accountId: string;
    folder: string;
    from: string;
    to: string;
    cc?: string;
    bcc?: string;
    subject: string;
    date: Date;
    body: string;
    html?: string;
    attachments: Attachment[];
    headers: any;
}

interface Attachment {
    filename: string;
    contentType: string;
    size: number;
    content: Buffer;
}

// Export types for TypeScript
export type { Email, Attachment };

// For CommonJS runtime
module.exports = {};

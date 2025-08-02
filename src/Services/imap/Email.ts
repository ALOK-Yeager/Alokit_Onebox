export interface Email {
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
    // AI properties for Elasticsearch
    aiCategory?: string;
    aiConfidence?: number;
    generatedReply?: string;
}

export interface Attachment {
    filename: string;
    contentType: string;
    size: number;
    content: Buffer;
}

// For CommonJS runtime (empty, as types are not exported at runtime)
module.exports = {};

export interface Email {
    id: string;
    uid: number;
    seqno: number;
    accountId: string;
    folder: string;
    subject: string;
    from: string;
    to: string;
    cc?: string;
    bcc?: string;
    date: Date;
    body: string;
    html?: string;
    attachments: Array<{
        filename: string;
        contentType: string;
        size: number;
        content?: Buffer;
    }>;
    headers: {
        [key: string]: string | string[];
    };
}
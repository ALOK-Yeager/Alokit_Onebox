declare module 'mailparser' {
    import { Readable } from 'stream';

    export interface ParsedMail {
        text?: string;
        html?: string;
        textAsHtml?: string;
        subject?: string;
        date?: Date;
        to?: Address | Address[];
        from?: Address;
        cc?: Address | Address[];
        bcc?: Address | Address[];
        messageId?: string;
        inReplyTo?: string;
        replyTo?: Address | Address[];
        references?: string | string[];
        headers?: Map<string, string | string[]>;
        attachments?: Attachment[];
    }

    export interface Address {
        value: AddressObject[];
        html: string;
        text: string;
    }

    export interface AddressObject {
        address: string;
        name: string;
    }

    export interface Attachment {
        type: string;
        content: Buffer;
        contentType: string;
        partId: string;
        release: () => void;
        contentDisposition: string;
        filename: string;
        headers: Map<string, string | string[]>;
        checksum: string;
        size: number;
        contentId: string;
        cid: string;
        related: boolean;
    }

    export function simpleParser(
        stream: string | Buffer | Readable,
        options?: { [key: string]: any }
    ): Promise<ParsedMail>;
}

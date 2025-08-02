declare global {
    namespace NodeJS {
        interface ProcessEnv {
            IMAP_SERVER: string;
            IMAP_PORT: string;
            IMAP_USER: string;
            IMAP_PASSWORD: string;
            IMAP_TLS: string;
        }
    }
}

export { }

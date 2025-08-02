interface AccountConfig {
    id: string;
    email: string;
    password: string;
    host: string;
    port: number;
    tls: boolean;
}

// Export the type for TypeScript
export type { AccountConfig };

// For CommonJS runtime
module.exports = {};
/**
 * Email Connection Modal Component
 * ==================================
 * 
 * Secure modal for connecting user email accounts to Onebox Aggregator.
 * 
 * Features:
 * - Provider selection with auto-detection
 * - Secure credential input
 * - Real-time validation
 * - Progress indication
 * - Error handling with user-friendly messages
 * - Security warnings
 * 
 * Security Considerations:
 * - Never stores passwords in component state longer than necessary
 * - Clears password from memory after submission
 * - Shows security warnings and best practices
 * - Recommends app passwords over main passwords
 * 
 * @author Onebox Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';

interface EmailConnectModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (connection: EmailConnection) => void;
}

interface EmailConnection {
    id: string;
    email_address: string;
    provider: string;
    status: string;
    created_at: string;
}

interface Provider {
    name: string;
    help_text: string;
    requires_oauth: boolean;
    custom: boolean;
}

const EmailConnectModal: React.FC<EmailConnectModalProps> = ({
    isOpen,
    onClose,
    onSuccess,
}) => {
    // Form state
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [provider, setProvider] = useState('Gmail');
    const [customServer, setCustomServer] = useState('');
    const [customPort, setCustomPort] = useState('993');

    // UI state
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle');
    const [providers, setProviders] = useState<Record<string, Provider>>({});
    const [showPassword, setShowPassword] = useState(false);

    // Load available providers on mount
    useEffect(() => {
        loadProviders();
    }, []);

    // Auto-detect provider from email address
    useEffect(() => {
        if (email && email.includes('@')) {
            const domain = email.split('@')[1]?.toLowerCase();

            const domainMapping: Record<string, string> = {
                'gmail.com': 'Gmail',
                'googlemail.com': 'Gmail',
                'outlook.com': 'Outlook',
                'hotmail.com': 'Outlook',
                'live.com': 'Outlook',
                'yahoo.com': 'Yahoo',
                'ymail.com': 'Yahoo',
                'icloud.com': 'iCloud',
                'me.com': 'iCloud',
                'mac.com': 'iCloud',
            };

            const detectedProvider = domainMapping[domain];
            if (detectedProvider && detectedProvider !== provider) {
                setProvider(detectedProvider);
            }
        }
    }, [email]);

    // Load providers from API
    const loadProviders = async () => {
        try {
            const response = await fetch('/api/email/providers');
            const data = await response.json();
            setProviders(data);
        } catch (err) {
            console.error('Failed to load providers:', err);
        }
    };

    // Handle form submission
    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validation
        if (!email || !password) {
            setError('Please enter both email and password');
            return;
        }

        if (provider === 'Custom IMAP' && !customServer) {
            setError('Please enter IMAP server address');
            return;
        }

        setIsLoading(true);
        setError('');
        setConnectionStatus('connecting');

        try {
            // Call API to connect email
            const response = await fetch('/api/email/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`, // TODO: Use your auth system
                },
                body: JSON.stringify({
                    email,
                    password,
                    provider,
                    custom_imap_server: provider === 'Custom IMAP' ? customServer : null,
                    custom_imap_port: provider === 'Custom IMAP' ? parseInt(customPort) : 993,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to connect');
            }

            const connection: EmailConnection = await response.json();

            setConnectionStatus('success');

            // Clear sensitive data from memory
            setPassword('');

            // Show success briefly, then close
            setTimeout(() => {
                setIsLoading(false);
                onSuccess(connection);
                handleClose();
            }, 1500);

        } catch (err: any) {
            setConnectionStatus('error');
            setError(err.message || 'Failed to connect. Please check your credentials.');
            setIsLoading(false);
        }
    };

    // Handle modal close
    const handleClose = () => {
        // Clear all form data
        setEmail('');
        setPassword('');
        setProvider('Gmail');
        setCustomServer('');
        setCustomPort('993');
        setError('');
        setConnectionStatus('idle');
        setIsLoading(false);

        onClose();
    };

    if (!isOpen) return null;

    const currentProvider = providers[provider];

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                    <h2 className="text-2xl font-bold text-gray-900">Connect Email Account</h2>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        disabled={isLoading}
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Security Warning Banner */}
                <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
                    <div className="flex items-start">
                        <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <div className="text-sm text-blue-800">
                            <p className="font-semibold mb-1">Security Notice</p>
                            <ul className="list-disc list-inside space-y-1 text-blue-700">
                                <li>Your password is encrypted and never stored in plaintext</li>
                                <li>We recommend using App Passwords instead of your main password</li>
                                <li>Connection expires after 30 days for security</li>
                                <li>We never access sent items, drafts, or trash folders</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Form */}
                <form onSubmit={handleConnect} className="px-6 py-6 space-y-6">
                    {/* Provider Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email Provider
                        </label>
                        <select
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            disabled={isLoading}
                        >
                            {Object.keys(providers).map((providerName) => (
                                <option key={providerName} value={providerName}>
                                    {providerName}
                                </option>
                            ))}
                        </select>
                        {currentProvider?.help_text && (
                            <p className="mt-2 text-sm text-gray-600">
                                💡 {currentProvider.help_text}
                            </p>
                        )}
                    </div>

                    {/* Email Address */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email Address
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your.email@example.com"
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            disabled={isLoading}
                            required
                            autoComplete="email"
                        />
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Password / App Password
                        </label>
                        <div className="relative">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••••••"
                                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                disabled={isLoading}
                                required
                                autoComplete="current-password"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                disabled={isLoading}
                            >
                                {showPassword ? (
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                    </svg>
                                ) : (
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                        {currentProvider?.requires_oauth && (
                            <p className="mt-2 text-sm text-amber-600 flex items-start">
                                <svg className="w-4 h-4 mr-1 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                This provider requires an App Password. Do NOT use your regular account password.
                            </p>
                        )}
                    </div>

                    {/* Custom IMAP Settings (shown only for Custom IMAP) */}
                    {provider === 'Custom IMAP' && (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    IMAP Server
                                </label>
                                <input
                                    type="text"
                                    value={customServer}
                                    onChange={(e) => setCustomServer(e.target.value)}
                                    placeholder="imap.example.com"
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    disabled={isLoading}
                                    required={provider === 'Custom IMAP'}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Port
                                </label>
                                <input
                                    type="number"
                                    value={customPort}
                                    onChange={(e) => setCustomPort(e.target.value)}
                                    placeholder="993"
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                    disabled={isLoading}
                                    min="1"
                                    max="65535"
                                />
                            </div>
                        </>
                    )}

                    {/* Error Message */}
                    {error && connectionStatus === 'error' && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="flex items-start">
                                <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-red-800">{error}</p>
                                    <p className="text-sm text-red-700 mt-1">
                                        Need help? <a href="/docs/email-troubleshooting" className="underline font-medium">View troubleshooting guide</a>
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Success Message */}
                    {connectionStatus === 'success' && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex items-center">
                                <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                <p className="text-sm font-medium text-green-800">
                                    Successfully connected! Syncing emails in the background...
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Form Actions */}
                    <div className="flex justify-end space-x-3 pt-4">
                        <button
                            type="button"
                            onClick={handleClose}
                            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                            disabled={isLoading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || connectionStatus === 'success'}
                            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Connecting...
                                </>
                            ) : connectionStatus === 'success' ? (
                                'Connected!'
                            ) : (
                                'Connect Email'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EmailConnectModal;

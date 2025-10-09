/**
 * Email Connection Status Component
 * ===================================
 * 
 * Displays connected email accounts with status indicators and management actions.
 * 
 * Features:
 * - Real-time connection status
 * - Last sync timestamp
 * - Manual sync trigger
 * - Disconnect action
 * - Error state handling
 * 
 * @author Onebox Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';

interface EmailConnection {
    id: string;
    email_address: string;
    provider: string;
    status: string;
    last_sync_at: string | null;
    sync_enabled: boolean;
    created_at: string;
    updated_at: string;
}

interface ConnectionStatusProps {
    onConnectClick: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ onConnectClick }) => {
    const [connections, setConnections] = useState<EmailConnection[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [syncingIds, setSyncingIds] = useState<Set<string>>(new Set());

    // Load connections on mount
    useEffect(() => {
        loadConnections();

        // Refresh connections every 30 seconds
        const interval = setInterval(loadConnections, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadConnections = async () => {
        try {
            const response = await fetch('/api/email/connections', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to load connections');
            }

            const data = await response.json();
            setConnections(data);
            setError('');
        } catch (err) {
            console.error('Failed to load connections:', err);
            setError('Failed to load email connections');
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async (connectionId: string) => {
        if (!confirm('Are you sure you want to disconnect this email account?')) {
            return;
        }

        try {
            const response = await fetch(`/api/email/disconnect/${connectionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to disconnect');
            }

            // Remove from list
            setConnections(connections.filter(c => c.id !== connectionId));
        } catch (err) {
            console.error('Failed to disconnect:', err);
            alert('Failed to disconnect email account');
        }
    };

    const handleSync = async (connectionId: string) => {
        setSyncingIds(prev => new Set(prev).add(connectionId));

        try {
            const response = await fetch(`/api/email/sync/${connectionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to sync');
            }

            // Reload connections to get updated sync time
            setTimeout(() => {
                loadConnections();
                setSyncingIds(prev => {
                    const next = new Set(prev);
                    next.delete(connectionId);
                    return next;
                });
            }, 2000);
        } catch (err) {
            console.error('Failed to sync:', err);
            alert('Failed to sync email account');
            setSyncingIds(prev => {
                const next = new Set(prev);
                next.delete(connectionId);
                return next;
            });
        }
    };

    const formatLastSync = (lastSyncAt: string | null) => {
        if (!lastSyncAt) return 'Never';

        const date = new Date(lastSyncAt);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
        return `${Math.floor(diffMins / 1440)} days ago`;
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'connected':
                return 'bg-green-500';
            case 'error':
                return 'bg-red-500';
            case 'pending':
                return 'bg-yellow-500';
            default:
                return 'bg-gray-500';
        }
    };

    const getProviderIcon = (provider: string) => {
        const icons: Record<string, string> = {
            'Gmail': '📧',
            'Outlook': '📨',
            'Yahoo': '📬',
            'iCloud': '☁️',
            'Custom IMAP': '⚙️',
        };
        return icons[provider] || '📮';
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-md">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-gray-900">Connected Email Accounts</h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Manage your connected email accounts and sync status
                    </p>
                </div>
                <button
                    onClick={onConnectClick}
                    className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Connect Email
                </button>
            </div>

            {/* Error Message */}
            {error && (
                <div className="px-6 py-4 bg-red-50 border-b border-red-200">
                    <p className="text-sm text-red-800">{error}</p>
                </div>
            )}

            {/* Connections List */}
            {connections.length === 0 ? (
                <div className="px-6 py-12 text-center">
                    <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Email Accounts Connected</h3>
                    <p className="text-gray-600 mb-6 max-w-md mx-auto">
                        Connect your email accounts to start searching and organizing your inbox with AI-powered tools.
                    </p>
                    <button
                        onClick={onConnectClick}
                        className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                    >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Connect Your First Email
                    </button>
                </div>
            ) : (
                <div className="divide-y divide-gray-200">
                    {connections.map((connection) => (
                        <div key={connection.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center flex-1">
                                    {/* Provider Icon */}
                                    <div className="text-3xl mr-4">
                                        {getProviderIcon(connection.provider)}
                                    </div>

                                    {/* Connection Info */}
                                    <div className="flex-1">
                                        <div className="flex items-center">
                                            <h3 className="text-lg font-semibold text-gray-900 mr-3">
                                                {connection.email_address}
                                            </h3>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${connection.status === 'connected' ? 'bg-green-100 text-green-800' :
                                                    connection.status === 'error' ? 'bg-red-100 text-red-800' :
                                                        'bg-yellow-100 text-yellow-800'
                                                }`}>
                                                <span className={`w-2 h-2 ${getStatusColor(connection.status)} rounded-full mr-1.5`}></span>
                                                {connection.status}
                                            </span>
                                        </div>
                                        <div className="flex items-center mt-1 text-sm text-gray-600">
                                            <span className="mr-4">
                                                <span className="font-medium">Provider:</span> {connection.provider}
                                            </span>
                                            <span>
                                                <span className="font-medium">Last sync:</span> {formatLastSync(connection.last_sync_at)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center space-x-2 ml-4">
                                    {/* Sync Button */}
                                    <button
                                        onClick={() => handleSync(connection.id)}
                                        disabled={syncingIds.has(connection.id)}
                                        className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        title="Sync now"
                                    >
                                        {syncingIds.has(connection.id) ? (
                                            <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                            </svg>
                                        ) : (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                            </svg>
                                        )}
                                    </button>

                                    {/* Settings Button */}
                                    <button
                                        className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                        title="Settings"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        </svg>
                                    </button>

                                    {/* Disconnect Button */}
                                    <button
                                        onClick={() => handleDisconnect(connection.id)}
                                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                        title="Disconnect"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ConnectionStatus;

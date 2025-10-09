import React, { useState, useEffect } from 'react';

interface Email {
    id: string;
    subject: string;
    sender: string;
    snippet: string;
    category: string;
    timestamp: string;
}

const EmailSearchUI: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
    const [results, setResults] = useState<Email[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const categories = [
        'All',
        'Interested',
        'Spam',
        'Important',
        'Promotions',
        'Social',
        'Updates',
        'Forums'
    ];

    useEffect(() => {
        const fetchResults = async () => {
            setIsLoading(true);

            try {
                const response = await fetch(
                    `/api/emails/search?q=${encodeURIComponent(searchQuery)}&filters=${selectedFilters.join(',')}`
                );
                const data = await response.json();
                setResults(data.results || []);
            } catch (error) {
                console.error('Error fetching search results:', error);
                setResults([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchResults();
    }, [searchQuery, selectedFilters]);

    const handleFilterChange = (category: string) => {
        if (category === 'All') {
            setSelectedFilters([]);
        } else {
            if (selectedFilters.includes(category)) {
                setSelectedFilters(selectedFilters.filter(f => f !== category));
            } else {
                setSelectedFilters([...selectedFilters, category]);
            }
        }
    };

    const isFilterActive = (category: string) => {
        if (category === 'All') {
            return selectedFilters.length === 0;
        }
        return selectedFilters.includes(category);
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header with Search Bar */}
            <header className="bg-white shadow-sm p-4">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-2xl font-bold text-gray-800 mb-4">Email Search</h1>
                    <div className="relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search emails..."
                            className="w-full p-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <svg
                            className="absolute left-4 top-3.5 h-5 w-5 text-gray-400"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden max-w-7xl mx-auto w-full">
                {/* Sidebar with Filters */}
                <aside className="w-64 bg-white p-4 border-r border-gray-200 overflow-y-auto">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4">Categories</h2>
                    <div className="space-y-2">
                        {categories.map((category) => (
                            <button
                                key={category}
                                onClick={() => handleFilterChange(category)}
                                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${isFilterActive(category)
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
                    {isLoading ? (
                        <div className="flex justify-center items-center h-full">
                            <div className="text-center">
                                <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                                <p className="text-gray-600">Searching emails...</p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <h2 className="text-xl font-semibold text-gray-800">
                                    {results.length} Results
                                </h2>
                            </div>

                            {results.length === 0 ? (
                                <div className="text-center py-12">
                                    <svg
                                        className="mx-auto h-12 w-12 text-gray-400"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                        />
                                    </svg>
                                    <h3 className="mt-2 text-lg font-medium text-gray-900">No emails found</h3>
                                    <p className="mt-1 text-gray-500">
                                        Try adjusting your search query or filters
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {results.map((email) => (
                                        <div
                                            key={email.id}
                                            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
                                        >
                                            <div className="flex justify-between">
                                                <h3 className="font-semibold text-gray-900 truncate">
                                                    {email.subject}
                                                </h3>
                                                <span className="text-xs font-medium px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                                                    {email.category}
                                                </span>
                                            </div>
                                            <div className="flex items-center mt-1">
                                                <span className="text-sm font-medium text-gray-700">
                                                    {email.sender}
                                                </span>
                                                <span className="mx-2 text-gray-300">•</span>
                                                <span className="text-sm text-gray-500">
                                                    {new Date(email.timestamp).toLocaleDateString()}
                                                </span>
                                            </div>
                                            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                                                {email.snippet}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default EmailSearchUI;
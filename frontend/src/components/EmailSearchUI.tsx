import React, { useState, useEffect } from 'react';
import './EmailSearchUI.css';
import type { EmailResult } from '../types/email';
import { demoEmails } from '../data/demoEmails';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const buildApiUrl = (path: string) => {
    return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
};

const DEFAULT_QUERY = 'funding update';

const filterDemoEmails = (query: string, filters: string[]): EmailResult[] => {
    const normalizedQuery = query.toLowerCase();
    const activeFilters = filters.filter(filter => filter !== 'All');

    return demoEmails.filter(email => {
        const matchesQuery =
            email.subject.toLowerCase().includes(normalizedQuery) ||
            email.sender.toLowerCase().includes(normalizedQuery) ||
            email.snippet.toLowerCase().includes(normalizedQuery);

        const matchesCategory =
            activeFilters.length === 0 || activeFilters.includes(email.category);

        return matchesQuery && matchesCategory;
    });
};

const EmailSearchUI: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState<string>(DEFAULT_QUERY);
    const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
    const [results, setResults] = useState<EmailResult[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [latencyMs, setLatencyMs] = useState<number | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);
    const [usingDemoData, setUsingDemoData] = useState<boolean>(false);

    const categories = [
        'All',
        'Interested',
        'Important',
        'Promotions',
        'Social',
        'Updates',
        'Forums',
        'Spam'
    ];

    const quickQueries = [
        { label: 'Funding announcements', value: 'series a funding' },
        { label: 'Security alerts', value: 'suspicious login' },
        { label: 'Renewal deals', value: 'contract renewal pricing' },
        { label: 'Team announcements', value: 'all-hands update' }
    ];

    useEffect(() => {
        const trimmedQuery = searchQuery.trim();
        if (!trimmedQuery) {
            setResults([]);
            setErrorMessage(null);
            setUsingDemoData(false);
            return;
        }

        const controller = new AbortController();

        const fetchResults = async () => {
            setIsLoading(true);
            setErrorMessage(null);
            setUsingDemoData(false);
            setLatencyMs(null);

            try {
                const start = performance.now();
                const response = await fetch(
                    buildApiUrl(`/api/emails/search?q=${encodeURIComponent(trimmedQuery)}&filters=${selectedFilters.join(',')}`),
                    { signal: controller.signal }
                );

                if (!response.ok) {
                    throw new Error(`Search failed with status ${response.status}`);
                }

                const data = await response.json();
                const normalizedResults = data.results || data.emails || [];
                setResults(normalizedResults);
                setLatencyMs(Math.round(performance.now() - start));
                setLastUpdated(new Date().toISOString());
            } catch (error) {
                if (controller.signal.aborted) return;
                console.error('Error fetching search results:', error);
                setResults(filterDemoEmails(trimmedQuery, selectedFilters));
                setUsingDemoData(true);
                setErrorMessage('Live cluster is warming up. Showing the curated demo inbox so you can keep exploring.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchResults();
        return () => controller.abort();
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
        <div className="email-search">
            <header className="email-search__header">
                <div className="email-search__intro">
                    <p className="eyebrow">Live Demo</p>
                    <h2>Smart Email Search</h2>
                    <p>
                        Query every inbox thread with semantic search, intent detection, and AI-powered summaries so you can focus on the
                        replies that unlock revenue.
                    </p>
                    <div className="email-search__pills">
                        <span>Intent-based triage</span>
                        <span>Thread-level summaries</span>
                        <span>One search bar for every inbox</span>
                    </div>
                </div>
                <div className="email-search__input">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder='subject:"funding" AND label:urgent'
                        aria-label="Search emails"
                    />
                    <span className="email-search__icon" aria-hidden="true">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path
                                fillRule="evenodd"
                                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </span>
                    <div className="email-search__suggestions">
                        {quickQueries.map((chip) => (
                            <button key={chip.value} type="button" onClick={() => setSearchQuery(chip.value)}>
                                {chip.label}
                            </button>
                        ))}
                    </div>
                    {errorMessage && (
                        <p className="email-search__alert" role="status">
                            {errorMessage}
                        </p>
                    )}
                </div>
            </header>

            <div className="email-search__value-grid">
                <article>
                    <h4>Rep workflows</h4>
                    <p>Skim every prospect touchpoint, from first reply through legal, without tab hopping.</p>
                </article>
                <article>
                    <h4>Security & IT</h4>
                    <p>Bubble up credential resets, suspicious logins, and compliance notices before they escalate.</p>
                </article>
                <article>
                    <h4>Founder inbox</h4>
                    <p>Find investment updates, hiring referrals, or urgent partner emails in seconds.</p>
                </article>
            </div>

            <div className="email-search__body">
                <aside className="email-search__filters">
                    <h3>Categories</h3>
                    <p className="helper">Stack filters to refine intent.</p>
                    <div className="filter-list">
                        {categories.map((category) => (
                            <button
                                key={category}
                                type="button"
                                onClick={() => handleFilterChange(category)}
                                className={`filter-pill ${isFilterActive(category) ? 'filter-pill--active' : ''}`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>

                    <div className="helper-card">
                        <h4>Day-to-day superpowers</h4>
                        <ul>
                            <li>Prep for stand-ups with a single recap.</li>
                            <li>Answer onboarding tickets twice as fast.</li>
                            <li>Surface past negotiations before replying.</li>
                        </ul>
                    </div>

                    <div className="demo-credentials">
                        <h4>Demo inbox</h4>
                        <p>Streamed from Gmail so you can test in minutes.</p>
                        <div>
                            <span>Address</span>
                            <code>oneboxrender@gmail.com</code>
                        </div>
                        <div>
                            <span>App password</span>
                            <code>rcgdnmxcumwxfrqq</code>
                        </div>
                        <p className="helper">Use the Gmail app password field when connecting via IMAP.</p>
                    </div>
                </aside>

                <main className="email-search__results">
                    {isLoading ? (
                        <div className="email-search__empty">
                            <span className="spinner" aria-label="Loading" />
                            <p>Searching emails...</p>
                        </div>
                    ) : (
                        <>
                            <div className="email-search__results-meta">
                                <div>
                                    <p className="eyebrow">{usingDemoData ? 'Demo dataset' : 'Live Elastic index'}</p>
                                    <h3>{results.length} emails found</h3>
                                </div>
                                <div className="meta-badges">
                                    {!usingDemoData && latencyMs !== null && (
                                        <span className="badge">Latency {latencyMs} ms</span>
                                    )}
                                    {lastUpdated && (
                                        <span className="badge">Updated {new Date(lastUpdated).toLocaleTimeString()}</span>
                                    )}
                                </div>
                            </div>

                            {results.length === 0 ? (
                                <div className="email-search__empty">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                                        />
                                    </svg>
                                    <h4>No emails yet</h4>
                                    <p>Try a different query or enable more filters.</p>
                                </div>
                            ) : (
                                <div className="email-card__stack">
                                    {results.map((email) => (
                                        <article key={email.id} className="email-card">
                                            <div className="email-card__meta">
                                                <div>
                                                    <h4>{email.subject}</h4>
                                                    <p>
                                                        <span>{email.sender}</span>
                                                        <span className="divider" />
                                                        <span>{new Date(email.timestamp).toLocaleDateString()}</span>
                                                    </p>
                                                </div>
                                                <span className="email-card__chip">{email.category}</span>
                                            </div>
                                            <p className="email-card__snippet">{email.snippet}</p>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </main>
            </div>
        </div>
    );
};

export default EmailSearchUI;
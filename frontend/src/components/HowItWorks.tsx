import React from 'react';
import './HowItWorks.css';

const HowItWorks: React.FC = () => {
    return (
        <section className="how-it-works">
            <div className="container">
                <h2 className="section-title">How It Works</h2>
                <p className="section-subtitle">
                    Seamlessly aggregate, index, and search your emails with AI-powered precision.
                </p>

                <div className="steps-grid">
                    <div className="step-card">
                        <div className="step-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                            </svg>
                        </div>
                        <h3>1. IMAP Sync</h3>
                        <p>
                            Connect your email accounts via secure IMAP. The system listens for new emails in real-time using IDLE, ensuring your Onebox is always up-to-date.
                        </p>
                    </div>

                    <div className="step-card">
                        <div className="step-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                        </div>
                        <h3>2. Dual Indexing</h3>
                        <p>
                            Emails are processed and stored in two powerful engines: <strong>Elasticsearch</strong> for keyword matching and a <strong>Vector Database</strong> for semantic understanding.
                        </p>
                    </div>

                    <div className="step-card">
                        <div className="step-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <h3>3. Hybrid Search</h3>
                        <p>
                            Search using natural language. Our hybrid engine combines keyword scores and semantic vector similarity to find exactly what you're looking for, even if you don't know the exact words.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default HowItWorks;

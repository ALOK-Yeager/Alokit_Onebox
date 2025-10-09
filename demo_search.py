"""
Demo Search Service for Streamlit Cloud Deployment

A lightweight SQLite-based search service that replaces the full Elasticsearch
and VectorDB setup for cloud deployment. Uses sample emails and basic text
matching for demonstration purposes.
"""

import json
import os
import sqlite3
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DemoSearchService:
    """
    Demo search service using SQLite for Streamlit Cloud deployment.
    Provides basic keyword and semantic-like search over sample emails.
    """
    
    def __init__(self, db_path: str = "demo_emails.db"):
        """Initialize the demo search service with SQLite backend."""
        self.db_path = db_path
        self.emails = self._load_sample_emails()
        self._init_database()
        self._populate_database()
    
    def _load_sample_emails(self) -> List[Dict[str, Any]]:
        """Load sample emails from JSON file or create them if they don't exist."""
        demo_path = os.path.join(os.path.dirname(__file__), "demo_emails.json")
        
        if not os.path.exists(demo_path):
            emails = self._create_sample_emails()
            with open(demo_path, 'w') as f:
                json.dump(emails, f, indent=2)
            return emails
        
        try:
            with open(demo_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading demo emails: {e}. Creating new ones.")
            return self._create_sample_emails()
    
    def _create_sample_emails(self) -> List[Dict[str, Any]]:
        """Create realistic sample emails for demo purposes."""
        emails = [
            {
                "id": "demo_001",
                "from": "project-manager@techcorp.com",
                "to": "team@techcorp.com",
                "subject": "Q4 Project Timeline Update - Critical Deadlines",
                "date": "2024-10-05T14:30:00Z",
                "body": "Hi team, I wanted to update you on the Q4 project timeline. We've moved the API integration milestone to next week due to dependencies on the authentication service. The database migration is still on track for October 15th. Please review the updated Gantt chart and let me know if you have any concerns about your deliverables.",
                "aiCategory": "More Information",
                "body_snippet": "Hi team, I wanted to update you on the Q4 project timeline. We've moved the API integration milestone to next week..."
            },
            {
                "id": "demo_002",
                "from": "support@stripe.com",
                "to": "billing@yourcompany.com",
                "subject": "Stripe Account Verification Required - Action Needed",
                "date": "2024-10-04T10:15:00Z",
                "body": "Hello, We need additional verification for your Stripe account (acct_1234567890). To maintain compliance with financial regulations, please upload a government-issued ID and proof of address within 48 hours. Your account will be temporarily restricted until verification is complete.",
                "aiCategory": "Interested",
                "body_snippet": "Hello, We need additional verification for your Stripe account. To maintain compliance with financial regulations..."
            },
            {
                "id": "demo_003",
                "from": "noreply@github.com",
                "to": "dev@yourcompany.com",
                "subject": "Security Alert: New SSH Key Added to Your Account",
                "date": "2024-10-03T16:45:00Z",
                "body": "A new SSH key was added to your GitHub account @your-username. If this was you, you can safely ignore this email. If you did not add this key, please review your account security settings immediately. Key fingerprint: SHA256:abcd1234efgh5678ijkl9012mnop3456qrst7890",
                "aiCategory": "Interested",
                "body_snippet": "A new SSH key was added to your GitHub account. If this was you, you can safely ignore this email..."
            },
            {
                "id": "demo_004",
                "from": "hr@company.com",
                "to": "all@company.com",
                "subject": "Annual Performance Review Process - Schedule Your 1:1",
                "date": "2024-10-02T09:00:00Z",
                "body": "Dear Team, It's time for our annual performance review cycle. Please schedule your 1:1 meeting with your manager by October 15th. The review will cover your accomplishments, areas for growth, and goal setting for next year. Don't forget to complete your self-assessment form in the HR portal.",
                "aiCategory": "More Information",
                "body_snippet": "Dear Team, It's time for our annual performance review cycle. Please schedule your 1:1 meeting..."
            },
            {
                "id": "demo_005",
                "from": "marketing@newsletter.com",
                "to": "subscriber@email.com",
                "subject": "Weekly Tech Newsletter - AI Breakthroughs This Week",
                "date": "2024-10-01T12:00:00Z",
                "body": "This week in tech: OpenAI announces new multimodal capabilities, Google releases updated Gemini models, and Microsoft expands Azure AI services. Also featuring: startup funding roundup, open source project highlights, and upcoming tech conferences.",
                "aiCategory": "Not Interested",
                "body_snippet": "This week in tech: OpenAI announces new multimodal capabilities, Google releases updated Gemini models..."
            },
            {
                "id": "demo_006",
                "from": "ceo@startup.com",
                "to": "all-hands@startup.com",
                "subject": "Series A Funding Announcement - We Did It!",
                "date": "2024-09-30T17:30:00Z",
                "body": "Team, I'm thrilled to announce that we've successfully closed our Series A funding round at $15M! This investment will allow us to double our engineering team, expand to new markets, and accelerate product development. Celebrating at the office Friday at 5 PM - see you there!",
                "aiCategory": "Interested",
                "body_snippet": "Team, I'm thrilled to announce that we've successfully closed our Series A funding round at $15M!"
            },
            {
                "id": "demo_007",
                "from": "client@bigcorp.com",
                "to": "sales@yourcompany.com",
                "subject": "Contract Renewal Discussion - Pricing Questions",
                "date": "2024-09-29T14:20:00Z",
                "body": "Hi Sales Team, Our current contract expires in November and we're interested in renewal. However, we'd like to discuss the pricing structure for next year given the expanded scope of work. Can we schedule a call this week to review options?",
                "aiCategory": "Interested",
                "body_snippet": "Hi Sales Team, Our current contract expires in November and we're interested in renewal..."
            },
            {
                "id": "demo_008",
                "from": "security@bank.com",
                "to": "customer@email.com",
                "subject": "Suspicious Login Attempt Detected",
                "date": "2024-09-28T08:45:00Z",
                "body": "We detected a login attempt to your account from an unrecognized device in a different location. If this was you, please verify by clicking the link below. If not, please change your password immediately and enable two-factor authentication.",
                "aiCategory": "Interested",
                "body_snippet": "We detected a login attempt to your account from an unrecognized device in a different location..."
            },
            {
                "id": "demo_009",
                "from": "devtools@company.com",
                "to": "engineering@company.com",
                "subject": "New Development Environment Setup Guide",
                "date": "2024-09-27T11:15:00Z",
                "body": "Engineers, we've updated our development environment setup process. The new Docker-based approach reduces onboarding time from 2 days to 2 hours. Please review the updated documentation and migrate your local environment by next Friday.",
                "aiCategory": "More Information",
                "body_snippet": "Engineers, we've updated our development environment setup process. The new Docker-based approach..."
            },
            {
                "id": "demo_010",
                "from": "legal@vendor.com",
                "to": "procurement@yourcompany.com",
                "subject": "Updated Terms of Service - Review Required",
                "date": "2024-09-26T15:00:00Z",
                "body": "Our Terms of Service have been updated to reflect new data privacy regulations. Please review the changes, particularly sections 4.2 (Data Processing) and 7.1 (Liability). Your continued use of our services constitutes acceptance of these terms.",
                "aiCategory": "More Information",
                "body_snippet": "Our Terms of Service have been updated to reflect new data privacy regulations..."
            }
        ]
        return emails
    
    def _init_database(self):
        """Initialize SQLite database with emails table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    from_addr TEXT,
                    to_addr TEXT,
                    subject TEXT,
                    date TEXT,
                    body TEXT,
                    ai_category TEXT,
                    body_snippet TEXT
                )
            """)
            
            # Create full-text search index
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
                    id,
                    subject,
                    body,
                    content='emails',
                    content_rowid='rowid'
                )
            """)
    
    def _populate_database(self):
        """Populate database with sample emails if empty."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if emails already exist
            count = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
            if count > 0:
                return
            
            # Insert sample emails
            for email in self.emails:
                conn.execute("""
                    INSERT INTO emails (id, from_addr, to_addr, subject, date, body, ai_category, body_snippet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email["id"],
                    email["from"],
                    email["to"],
                    email["subject"],
                    email["date"],
                    email["body"],
                    email["aiCategory"],
                    email["body_snippet"]
                ))
                
                # Also insert into FTS table
                conn.execute("""
                    INSERT INTO emails_fts (id, subject, body)
                    VALUES (?, ?, ?)
                """, (email["id"], email["subject"], email["body"]))
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search emails using SQLite FTS and return formatted results.
        
        Args:
            query: Search query string
            n_results: Maximum number of results to return
            
        Returns:
            List of email dictionaries with search metadata
        """
        if not query.strip():
            return []
        
        results = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # First try FTS search
                fts_query = self._prepare_fts_query(query)
                cursor = conn.execute("""
                    SELECT e.*, fts.bm25(emails_fts) as score
                    FROM emails_fts fts
                    JOIN emails e ON e.id = fts.id
                    WHERE emails_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (fts_query, n_results))
                
                fts_results = cursor.fetchall()
                
                # If FTS doesn't return enough results, fall back to LIKE search
                if len(fts_results) < n_results:
                    like_query = f"%{query}%"
                    cursor = conn.execute("""
                        SELECT *, 0.5 as score
                        FROM emails
                        WHERE (subject LIKE ? OR body LIKE ?)
                        AND id NOT IN ({})
                        LIMIT ?
                    """.format(','.join(['?' for _ in fts_results])), 
                    [like_query, like_query] + [r['id'] for r in fts_results] + [n_results - len(fts_results)])
                    
                    like_results = cursor.fetchall()
                    all_results = list(fts_results) + list(like_results)
                else:
                    all_results = fts_results
                
                # Convert to the expected format
                for row in all_results[:n_results]:
                    result = {
                        "id": row["id"],
                        "from": row["from_addr"],
                        "to": row["to_addr"],
                        "subject": row["subject"],
                        "date": row["date"],
                        "body": row["body"],
                        "body_snippet": row["body_snippet"],
                        "aiCategory": row["ai_category"],
                        "score": float(row["score"]) if row["score"] else 0.0,
                        "match_type": "semantic" if row["score"] > 0.7 else "keyword"
                    }
                    results.append(result)
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Fallback to in-memory search
            results = self._fallback_search(query, n_results)
        
        return results
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5 search."""
        # Remove special characters and split into words
        words = re.findall(r'\w+', query.lower())
        if not words:
            return query
        
        # Create FTS query with OR operator
        return ' OR '.join(words)
    
    def _fallback_search(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        """Fallback search using in-memory data."""
        query_lower = query.lower()
        results = []
        
        for email in self.emails:
            score = 0.0
            match_type = "keyword"
            
            # Simple scoring based on matches
            if query_lower in email["subject"].lower():
                score += 0.8
                match_type = "semantic"
            if query_lower in email["body"].lower():
                score += 0.6
            
            # Check for partial word matches
            for word in query_lower.split():
                if word in email["subject"].lower() or word in email["body"].lower():
                    score += 0.3
            
            if score > 0:
                result = {
                    "id": email["id"],
                    "from": email["from"],
                    "to": email["to"],
                    "subject": email["subject"],
                    "date": email["date"],
                    "body": email["body"],
                    "body_snippet": email["body_snippet"],
                    "aiCategory": email["aiCategory"],
                    "score": score,
                    "match_type": match_type
                }
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific email by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "id": row["id"],
                        "from": row["from_addr"],
                        "to": row["to_addr"],
                        "subject": row["subject"],
                        "date": row["date"],
                        "body": row["body"],
                        "body_snippet": row["body_snippet"],
                        "aiCategory": row["ai_category"]
                    }
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total_emails = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
                categories = conn.execute("""
                    SELECT ai_category, COUNT(*) as count 
                    FROM emails 
                    GROUP BY ai_category
                """).fetchall()
                
                return {
                    "total_emails": total_emails,
                    "categories": dict(categories),
                    "demo_mode": True
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_emails": len(self.emails), "demo_mode": True}


# Convenience function for easy import
def create_demo_search_service() -> DemoSearchService:
    """Create and return a demo search service instance."""
    return DemoSearchService()


if __name__ == "__main__":
    # Test the demo search service
    service = DemoSearchService()
    
    print("Demo Search Service Test")
    print("=" * 30)
    
    # Test search
    queries = [
        "project timeline",
        "stripe account",
        "security alert",
        "funding announcement"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = service.search(query, n_results=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['subject']} (Score: {result['score']:.2f})")
    
    # Test stats
    print(f"\nStats: {service.get_stats()}")
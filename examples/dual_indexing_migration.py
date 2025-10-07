"""
Email Indexing Migration Guide and Examples

This module provides examples for migrating from ElasticsearchService to the new
dual indexing pipeline with VectorDB support, transaction safety, and batch processing.

Migration Path:
1. Start VectorDB service: python vectordb_service.py
2. Replace ElasticsearchService with DualIndexingAdapter
3. Test dual indexing with backward compatibility
4. Enable advanced features (batch processing, transaction safety)
5. Monitor performance and health metrics

Examples:
- Basic migration (drop-in replacement)
- Batch indexing for high-throughput scenarios
- Transaction safety and rollback testing
- Health monitoring and statistics
- Error handling and recovery patterns
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any

# For TypeScript integration examples
typescript_examples = """
// TypeScript Integration Examples

// 1. Basic Migration - Drop-in Replacement
// BEFORE:
import { ElasticsearchService } from '../Services/search/ElasticsearchService';
const searchService = new ElasticsearchService();

// AFTER:
import { DualIndexingAdapter } from '../Services/search/DualIndexingAdapter';
const searchService = new DualIndexingAdapter();
// All existing code continues to work unchanged!

// 2. Enhanced Migration with New Features
import { EmailIndexingService } from '../Services/search/EmailIndexingService';

const indexingService = new EmailIndexingService({
    enableVectorDB: true,
    enableElasticsearch: true,
    enableTransactionSafety: true,
    batchSize: 50,
    maxRetries: 3,
    retryDelayMs: 1000,
    vectorDBEndpoint: 'http://localhost:8001',
    progressCallback: (progress) => {
        console.log(`Progress: ${progress.processed}/${progress.total} (${progress.successful} successful)`);
    }
});

// 3. Batch Processing Example
async function batchIndexEmails(emails: Email[]) {
    console.log(`Starting batch indexing of ${emails.length} emails...`);
    
    const result = await indexingService.indexEmails(emails);
    
    console.log('Batch Indexing Results:');
    console.log(`- Total Processed: ${result.totalProcessed}`);
    console.log(`- Successful: ${result.totalSuccessful}`);
    console.log(`- Failed: ${result.totalFailed}`);
    console.log(`- Elasticsearch Success: ${result.elasticsearchSuccessful}`);
    console.log(`- VectorDB Success: ${result.vectorDBSuccessful}`);
    console.log(`- Processing Time: ${result.totalProcessingTimeMs}ms`);
    
    if (result.errors.length > 0) {
        console.error('Errors encountered:', result.errors);
    }
    
    return result;
}

// 4. Health Monitoring
async function monitorServiceHealth() {
    const health = await indexingService.healthCheck();
    const stats = indexingService.getStats();
    
    console.log('Service Health:', health);
    console.log('Service Statistics:', stats);
    
    if (!health.overall) {
        console.error('Service health degraded!');
        // Implement alerting logic
    }
}

// 5. Progressive Enhancement
async function enableDualIndexingGradually() {
    const adapter = new DualIndexingAdapter();
    
    // Check current capabilities
    const capabilities = adapter.getCapabilities();
    console.log('Current capabilities:', capabilities);
    
    if (!capabilities.dualIndexing) {
        console.log('Attempting to enable dual indexing...');
        const success = await adapter.enableDualIndexing({
            enableVectorDB: true,
            enableTransactionSafety: true,
            batchSize: 20
        });
        
        if (success) {
            console.log('Dual indexing enabled successfully!');
        } else {
            console.log('Dual indexing failed to enable, continuing with Elasticsearch only');
        }
    }
}

// 6. Error Handling and Recovery
async function robustEmailIndexing(email: Email) {
    try {
        const result = await indexingService.indexEmail(email);
        
        if (result.success) {
            console.log(`Email ${email.id} indexed successfully`);
        } else {
            console.error(`Email ${email.id} indexing failed:`, result.errors);
            
            // Implement fallback strategy
            if (!result.elasticsearchSuccess && !result.vectorDBSuccess) {
                // Total failure - retry with different configuration
                console.log('Retrying with Elasticsearch only...');
                const fallbackService = new ElasticsearchService();
                await fallbackService.indexEmail(email);
            }
        }
        
        return result;
    } catch (error) {
        console.error('Unexpected indexing error:', error);
        throw error;
    }
}

// 7. Integration with Existing IMAP Service
// In ImapService.ts, replace the onEmailReceived callback:

// BEFORE:
const esService = new ElasticsearchService();
const onEmailReceived = async (email: Email) => {
    await esService.indexEmail(email);
};

// AFTER:
const indexingService = new DualIndexingAdapter();
const onEmailReceived = async (email: Email) => {
    await indexingService.indexEmail(email);  // Same interface!
};

// Or with enhanced error handling:
const onEmailReceived = async (email: Email) => {
    try {
        if (indexingService.getCapabilities().dualIndexing) {
            const result = await (indexingService as EmailIndexingService).indexEmail(email);
            if (!result.success) {
                logger.warn(`Partial indexing failure for ${email.id}:`, result.errors);
            }
        } else {
            await indexingService.indexEmail(email);
        }
    } catch (error) {
        logger.error(`Email indexing failed for ${email.id}:`, error);
        // Don't throw - let email processing continue
    }
};
"""

# Python examples for VectorDB service setup and testing
def start_vectordb_service():
    """Example of starting the VectorDB service"""
    print("Starting VectorDB service...")
    print("Run: uvicorn vectordb_service:app --host 0.0.0.0 --port 8001")
    print("Service will be available at: http://localhost:8001")
    print("API docs available at: http://localhost:8001/docs")

async def test_vectordb_service():
    """Test the VectorDB service endpoints"""
    import aiohttp
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        async with session.get(f"{base_url}/health") as resp:
            health = await resp.json()
            print("Health check:", health)
        
        # Test adding an email
        email_data = {
            "email_id": "test-email-1",
            "content": "This is a test email about machine learning and AI"
        }
        
        async with session.post(f"{base_url}/add_email", json=email_data) as resp:
            result = await resp.json()
            print("Add email result:", result)
        
        # Test search
        async with session.get(f"{base_url}/search?q=machine learning&n_results=5") as resp:
            search_results = await resp.json()
            print("Search results:", search_results)
        
        # Test deletion (for rollback testing)
        delete_data = {"email_id": "test-email-1"}
        async with session.post(f"{base_url}/delete_email", json=delete_data) as resp:
            delete_result = await resp.json()
            print("Delete result:", delete_result)
        
        # Test statistics
        async with session.get(f"{base_url}/stats") as resp:
            stats = await resp.json()
            print("Service stats:", stats)

def test_vectordb_locally():
    """Test VectorDB class locally without service"""
    import sys
    import os
    # Make absolute path to ensure correct resolution
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'Services', 'search'))
    sys.path.append(module_path)
    try:
        from VectorDB import VectorDB
    except ImportError:
        print(f"Error: VectorDB module not found in {module_path}")
        print("Please ensure the VectorDB.py file exists in that location")
        return
    
    print("Testing VectorDB locally...")
    
    # Initialize VectorDB
    vectordb = VectorDB(persist_directory="./test_vector_store")
    
    # Add test emails
    test_emails = [
        ("email-1", "Meeting scheduled for project review tomorrow"),
        ("email-2", "Invoice for software license renewal"),
        ("email-3", "Travel booking confirmation for business trip"),
        ("email-4", "Security alert: suspicious login attempt"),
        ("email-5", "Newsletter: Latest AI developments")
    ]
    
    print(f"Adding {len(test_emails)} test emails...")
    email_ids = [e[0] for e in test_emails]
    contents = [e[1] for e in test_emails]
    
    vectordb.add_emails(email_ids, contents)
    print(f"Vector store now contains {len(vectordb)} emails")
    
    # Test search
    search_queries = [
        "meeting project",
        "payment invoice",
        "travel booking",
        "security alert",
        "artificial intelligence"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = vectordb.search(query, n_results=3)
        for i, result in enumerate(results):
            print(f"  {i+1}. ID: {result['ids'][0]}, Score: {result['distances'][0]:.3f}")
            print(f"     Content: {result['documents'][0][:50]}...")
    
    # Test deletion
    print(f"\nTesting deletion...")
    success = vectordb.delete_email("email-1")
    print(f"Delete email-1: {success}")
def performance_benchmark():
    """Benchmark the dual indexing performance"""
    import sys
    import os
    # Make absolute path to ensure correct resolution
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'Services', 'search'))
    sys.path.append(module_path)
    try:
        from VectorDB import VectorDB
    except ImportError:
        print(f"Error: VectorDB module not found in {module_path}")
        print("Please ensure the VectorDB.py file exists in that location")
        return

def performance_benchmark():
    """Benchmark the dual indexing performance"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'Services', 'search'))
    from VectorDB import VectorDB
    import random
    import string
    
    print("Running performance benchmark...")
    
    vectordb = VectorDB(persist_directory="./benchmark_vector_store")
    
    # Generate test data
    def generate_email_content():
        subjects = [
            "Meeting invitation", "Project update", "Invoice payment",
            "Security alert", "Newsletter", "Travel booking",
            "Support ticket", "Marketing campaign", "Legal notice"
        ]
        
        bodies = [
            "Please review the attached documents and provide feedback",
            "The quarterly results are now available for review",
            "Your payment is due in 5 days",
            "Suspicious activity detected on your account",
            "Latest industry news and updates",
            "Your booking has been confirmed"
        ]
        
        subject = random.choice(subjects)
        body = random.choice(bodies)
        return f"{subject}. {body}"
    
    # Benchmark single email indexing
    print("\nBenchmark: Single email indexing")
    times = []
    for i in range(100):
        email_id = f"bench-{i}"
        content = generate_email_content()
        
        start_time = time.time()
        vectordb.add_email(email_id, content)
        end_time = time.time()
        
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    print(f"Average time per email: {avg_time*1000:.2f}ms")
    print(f"Throughput: {1/avg_time:.1f} emails/second")
    
    # Benchmark batch indexing
    print("\nBenchmark: Batch email indexing")
    batch_emails = []
    for i in range(100, 200):
        batch_emails.append((f"batch-{i}", generate_email_content()))
    
    start_time = time.time()
    email_ids = [e[0] for e in batch_emails]
    contents = [e[1] for e in batch_emails]
    vectordb.add_emails(email_ids, contents)
    end_time = time.time()
    
    batch_time = end_time - start_time
    batch_avg = batch_time / len(batch_emails)
    print(f"Batch time for {len(batch_emails)} emails: {batch_time:.2f}s")
    print(f"Average time per email in batch: {batch_avg*1000:.2f}ms")
    print(f"Batch throughput: {len(batch_emails)/batch_time:.1f} emails/second")
    
    # Benchmark search
    print("\nBenchmark: Search performance")
    search_queries = [
        "meeting project review",
        "payment invoice due",
        "security suspicious activity",
        "travel booking confirmation",
        "marketing campaign update"
    ]
    
    search_times = []
    for query in search_queries:
        start_time = time.time()
        results = vectordb.search(query, n_results=10)
        end_time = time.time()
        
        search_times.append(end_time - start_time)
        print(f"Query '{query}': {len(results)} results in {(end_time-start_time)*1000:.2f}ms")
    
    avg_search_time = sum(search_times) / len(search_times)
    print(f"Average search time: {avg_search_time*1000:.2f}ms")
    
    print(f"\nFinal vector store size: {len(vectordb)} emails")

def deployment_checklist():
    """Deployment checklist and best practices"""
    checklist = """
    🚀 Email Dual Indexing Deployment Checklist

    Pre-deployment:
    ☐ Install dependencies: pip install -r python-requirements.txt
    ☐ Configure environment variables in .env:
        - VECTORDB_ENDPOINT=http://localhost:8001
        - ENABLE_VECTORDB=true  
        - TRANSACTION_SAFETY=true
        - INDEXING_BATCH_SIZE=20
    ☐ Test VectorDB service locally: python vectordb_service.py
    ☐ Verify service health: curl http://localhost:8001/health
    ☐ Run integration tests: python examples/dual_indexing_examples.py

    Deployment Steps:
    ☐ Start VectorDB service in production:
        uvicorn vectordb_service:app --host 0.0.0.0 --port 8001 --workers 4
    ☐ Update TypeScript services to use DualIndexingAdapter
    ☐ Monitor logs for dual indexing initialization
    ☐ Verify both Elasticsearch and VectorDB are receiving data
    ☐ Check health endpoints for service status

    Post-deployment Monitoring:
    ☐ Monitor service health: GET /api/emails/health
    ☐ Track indexing statistics: GET /api/emails/service/status  
    ☐ Check error rates in logs
    ☐ Monitor VectorDB service metrics: GET /stats
    ☐ Verify search functionality with both keyword and semantic queries

    Performance Optimization:
    ☐ Adjust batch sizes based on throughput requirements
    ☐ Configure retry policies for resilience
    ☐ Monitor memory usage of VectorDB service
    ☐ Scale VectorDB service horizontally if needed
    ☐ Optimize embedding model based on your email content

    Rollback Plan:
    ☐ Keep ElasticsearchService as fallback option
    ☐ Use DualIndexingAdapter.disableDualIndexing() if issues arise
    ☐ Monitor for any indexing failures during transition
    ☐ Have database backups ready
    ☐ Document rollback procedures for team

    Security Considerations:
    ☐ Secure VectorDB service endpoints
    ☐ Use HTTPS in production
    ☐ Implement rate limiting
    ☐ Monitor for unauthorized access
    ☐ Encrypt sensitive email content if required
    """
    
    print(checklist)

if __name__ == "__main__":
    print("Email Dual Indexing Migration Examples")
    print("=====================================")
    
    print("\n1. TypeScript Integration Examples:")
    print(typescript_examples)
    
    print("\n2. Starting VectorDB Service:")
    start_vectordb_service()
    
    print("\n3. Testing VectorDB Service (run after starting service):")
    print("asyncio.run(test_vectordb_service())")
    
    print("\n4. Testing VectorDB Locally:")
    test_vectordb_locally()
    
    print("\n5. Performance Benchmark:")
    performance_benchmark()
    
    print("\n6. Deployment Checklist:")
    deployment_checklist()
    
    print("\n🎉 Migration examples completed!")
    print("Next steps:")
    print("1. Start the VectorDB service: python vectordb_service.py")
    print("2. Update your TypeScript code to use DualIndexingAdapter") 
    print("3. Test the dual indexing functionality")
    print("4. Monitor health and performance metrics")
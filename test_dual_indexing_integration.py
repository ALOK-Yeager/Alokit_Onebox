#!/usr/bin/env python3
"""
Comprehensive Integration Test for Dual Email Indexing Pipeline

This script tests the complete email indexing pipeline including:
- VectorDB service functionality
- Elasticsearch integration
- Transaction safety and rollback mechanisms
- Batch processing capabilities
- Error handling and recovery
- Performance characteristics

Usage:
    python test_dual_indexing_integration.py

Prerequisites:
    1. VectorDB service running: python vectordb_service.py
    2. Elasticsearch running on localhost:9200
    3. Dependencies installed: pip install -r python-requirements.txt
"""

import asyncio
import json
import random
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

import aiohttp
import requests

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'Services', 'search'))

class IntegrationTester:
    def __init__(self):
        self.vectordb_url = "http://localhost:8001"
        self.elasticsearch_url = "http://localhost:9200"
        self.test_results = {
            "vectordb_service": False,
            "elasticsearch_service": False,
            "basic_indexing": False,
            "batch_indexing": False,
            "search_functionality": False,
            "rollback_mechanism": False,
            "error_handling": False,
            "performance_acceptable": False
        }
        self.test_emails = []
        self.generate_test_data()

    def generate_test_data(self):
        """Generate test email data"""
        subjects = [
            "Meeting invitation for project review",
            "Invoice payment due tomorrow", 
            "Security alert: suspicious login",
            "Travel booking confirmation",
            "Newsletter: AI developments",
            "Support ticket #12345",
            "Marketing campaign results",
            "Legal notice: policy update",
            "Performance review scheduled",
            "Budget approval request"
        ]
        
        bodies = [
            "Please join us for the quarterly review meeting tomorrow at 2 PM in conference room A.",
            "Your monthly subscription payment of $99.99 is due tomorrow. Please update your payment method.",
            "We detected a suspicious login attempt from IP 192.168.1.100. Please verify this was you.",
            "Your flight booking is confirmed. Flight AA123 departing at 10:30 AM from JFK to LAX.",
            "Stay updated with the latest developments in artificial intelligence and machine learning.",
            "Your support request has been received. Our team will respond within 24 hours.",
            "Our recent email campaign achieved a 15% open rate and 3% click-through rate.",
            "We have updated our privacy policy. Please review the changes before your next login.",
            "Your annual performance review is scheduled for next week. Please prepare your self-assessment.",
            "The budget request for Q4 marketing initiatives requires your approval by Friday."
        ]
        
        for i in range(10):
            email_id = f"test-email-{i+1}"
            subject = subjects[i]
            body = bodies[i]
            content = f"{subject}\n\n{body}"
            
            self.test_emails.append({
                "email_id": email_id,
                "subject": subject,
                "body": body,
                "content": content
            })

    async def test_vectordb_service(self) -> bool:
        """Test VectorDB service availability and basic functionality"""
        print("🔍 Testing VectorDB service...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.vectordb_url}/health") as resp:
                    if resp.status != 200:
                        print(f"❌ VectorDB health check failed: {resp.status}")
                        return False
                    
                    health_data = await resp.json()
                    if not health_data.get("vector_db_available"):
                        print("❌ VectorDB not available")
                        return False
                
                # Test basic add/search/delete operations
                test_email = self.test_emails[0]
                
                # Add email
                async with session.post(f"{self.vectordb_url}/add_email", json=test_email) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to add email: {resp.status}")
                        return False
                
                # Search for email
                async with session.get(f"{self.vectordb_url}/search?q=meeting&n_results=5") as resp:
                    if resp.status != 200:
                        print(f"❌ Search failed: {resp.status}")
                        return False
                    
                    search_data = await resp.json()
                    if not search_data.get("success"):
                        print("❌ Search returned unsuccessful")
                        return False
                
                # Delete email (cleanup)
                async with session.post(f"{self.vectordb_url}/delete_email", 
                                      json={"email_id": test_email["email_id"]}) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to delete email: {resp.status}")
                        return False
                
                print("✅ VectorDB service tests passed")
                return True
                
        except Exception as e:
            print(f"❌ VectorDB service test failed: {e}")
            return False

    def test_elasticsearch_service(self) -> bool:
        """Test Elasticsearch availability"""
        print("🔍 Testing Elasticsearch service...")
        
        try:
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                if health.get("status") in ["green", "yellow"]:
                    print("✅ Elasticsearch service available")
                    return True
                else:
                    print(f"❌ Elasticsearch cluster status: {health.get('status')}")
                    return False
            else:
                print(f"❌ Elasticsearch health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Elasticsearch service test failed: {e}")
            return False

    async def test_batch_indexing(self) -> bool:
        """Test batch indexing functionality"""
        print("🔍 Testing batch indexing...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare batch data
                batch_emails = [
                    {"email_id": email["email_id"], "content": email["content"]}
                    for email in self.test_emails[:5]
                ]
                
                # Send batch request
                async with session.post(f"{self.vectordb_url}/add_emails", 
                                      json={"emails": batch_emails}) as resp:
                    if resp.status != 200:
                        print(f"❌ Batch indexing failed: {resp.status}")
                        return False
                    
                    batch_result = await resp.json()
                    if not batch_result.get("success"):
                        print("❌ Batch indexing returned unsuccessful")
                        return False
                    
                    if batch_result.get("successful", 0) != len(batch_emails):
                        print(f"❌ Not all emails indexed: {batch_result}")
                        return False
                
                print("✅ Batch indexing tests passed")
                return True
                
        except Exception as e:
            print(f"❌ Batch indexing test failed: {e}")
            return False

    async def test_search_functionality(self) -> bool:
        """Test search across different query types"""
        print("🔍 Testing search functionality...")
        
        try:
            async with aiohttp.ClientSession() as session:
                search_queries = [
                    ("meeting", 1),  # Should find meeting invitation
                    ("payment invoice", 1),  # Should find invoice email
                    ("security", 1),  # Should find security alert
                    ("nonexistent query xyz", 0)  # Should find nothing
                ]
                
                for query, expected_min_results in search_queries:
                    async with session.get(f"{self.vectordb_url}/search?q={query}&n_results=10") as resp:
                        if resp.status != 200:
                            print(f"❌ Search failed for '{query}': {resp.status}")
                            return False
                        
                        search_result = await resp.json()
                        if not search_result.get("success"):
                            print(f"❌ Search unsuccessful for '{query}'")
                            return False
                        
                        results_count = len(search_result.get("results", []))
                        if results_count < expected_min_results:
                            print(f"❌ Search for '{query}' returned {results_count} results, expected at least {expected_min_results}")
                            return False
                
                print("✅ Search functionality tests passed")
                return True
                
        except Exception as e:
            print(f"❌ Search functionality test failed: {e}")
            return False

    async def test_rollback_mechanism(self) -> bool:
        """Test rollback and delete functionality"""
        print("🔍 Testing rollback mechanism...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Add an email first
                test_email = self.test_emails[0]
                async with session.post(f"{self.vectordb_url}/add_email", json=test_email) as resp:
                    if resp.status != 200:
                        print("❌ Failed to add email for rollback test")
                        return False
                
                # Verify it exists
                async with session.get(f"{self.vectordb_url}/search?q=meeting&n_results=5") as resp:
                    search_result = await resp.json()
                    initial_count = len(search_result.get("results", []))
                
                # Delete the email (simulate rollback)
                async with session.post(f"{self.vectordb_url}/delete_email", 
                                      json={"email_id": test_email["email_id"]}) as resp:
                    if resp.status != 200:
                        print(f"❌ Failed to delete email: {resp.status}")
                        return False
                    
                    delete_result = await resp.json()
                    if not delete_result.get("success"):
                        print("❌ Delete operation unsuccessful")
                        return False
                
                # Verify it's gone
                await asyncio.sleep(1)  # Give time for deletion to propagate
                async with session.get(f"{self.vectordb_url}/search?q=meeting&n_results=5") as resp:
                    search_result = await resp.json()
                    final_count = len(search_result.get("results", []))
                
                if final_count >= initial_count:
                    print("❌ Email was not properly deleted")
                    return False
                
                print("✅ Rollback mechanism tests passed")
                return True
                
        except Exception as e:
            print(f"❌ Rollback mechanism test failed: {e}")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling for various failure scenarios"""
        print("🔍 Testing error handling...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test invalid requests
                test_cases = [
                    # Missing email_id
                    (f"{self.vectordb_url}/add_email", {"content": "test"}, 400),
                    # Empty search query should be handled gracefully
                    (f"{self.vectordb_url}/search?q=&n_results=5", None, 400),
                    # Invalid n_results
                    (f"{self.vectordb_url}/search?q=test&n_results=1000", None, 400),
                ]
                
                for url, data, expected_status in test_cases:
                    if data:
                        async with session.post(url, json=data) as resp:
                            if resp.status != expected_status:
                                print(f"❌ Expected status {expected_status}, got {resp.status} for {url}")
                                return False
                    else:
                        async with session.get(url) as resp:
                            if resp.status != expected_status:
                                print(f"❌ Expected status {expected_status}, got {resp.status} for {url}")
                                return False
                
                print("✅ Error handling tests passed")
                return True
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False

    async def test_performance(self) -> bool:
        """Test performance characteristics"""
        print("🔍 Testing performance...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test single email indexing performance
                start_time = time.time()
                test_email = {
                    "email_id": "perf-test-1",
                    "content": "Performance test email content for measuring indexing speed"
                }
                
                async with session.post(f"{self.vectordb_url}/add_email", json=test_email) as resp:
                    if resp.status != 200:
                        print("❌ Performance test indexing failed")
                        return False
                
                single_time = time.time() - start_time
                
                # Test search performance
                start_time = time.time()
                async with session.get(f"{self.vectordb_url}/search?q=performance&n_results=10") as resp:
                    if resp.status != 200:
                        print("❌ Performance test search failed")
                        return False
                
                search_time = time.time() - start_time
                
                # Cleanup
                await session.post(f"{self.vectordb_url}/delete_email", 
                                 json={"email_id": "perf-test-1"})
                
                # Performance thresholds (adjust based on requirements)
                if single_time > 5.0:  # 5 seconds max for single email
                    print(f"❌ Single email indexing too slow: {single_time:.2f}s")
                    return False
                
                if search_time > 2.0:  # 2 seconds max for search
                    print(f"❌ Search too slow: {search_time:.2f}s")
                    return False
                
                print(f"✅ Performance tests passed (indexing: {single_time:.2f}s, search: {search_time:.2f}s)")
                return True
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False

    async def cleanup_test_data(self):
        """Clean up any remaining test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            async with aiohttp.ClientSession() as session:
                email_ids = [email["email_id"] for email in self.test_emails]
                await session.post(f"{self.vectordb_url}/delete_emails", 
                                 json={"email_ids": email_ids})
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting Dual Email Indexing Integration Tests")
        print("=" * 50)
        
        # Test order matters - services must be available first
        tests = [
            ("vectordb_service", self.test_vectordb_service()),
            ("elasticsearch_service", self.test_elasticsearch_service()),
            ("batch_indexing", self.test_batch_indexing()),
            ("search_functionality", self.test_search_functionality()),
            ("rollback_mechanism", self.test_rollback_mechanism()),
            ("error_handling", self.test_error_handling()),
            ("performance_acceptable", self.test_performance())
        ]
        
        for test_name, test_coro in tests:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            self.test_results[test_name] = result
            
            if not result:
                print(f"💥 Test failed: {test_name}")
                break  # Stop on first failure for faster feedback
        
        # Cleanup regardless of test results
        await self.cleanup_test_data()
        
        return self.test_results

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("📊 Integration Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print("-" * 50)
        print(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Dual indexing system is ready for deployment.")
            return True
        else:
            print("⚠️ Some tests failed. Please review the issues above before deployment.")
            return False

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    
    try:
        results = await tester.run_all_tests()
        success = tester.print_summary()
        
        if success:
            print("\n🚀 Next steps:")
            print("1. Deploy VectorDB service to production")
            print("2. Update TypeScript services to use DualIndexingAdapter")
            print("3. Monitor logs and health endpoints")
            print("4. Gradually increase dual indexing usage")
            return 0
        else:
            print("\n🔧 Troubleshooting:")
            print("1. Ensure VectorDB service is running: python vectordb_service.py")
            print("2. Verify Elasticsearch is running on localhost:9200")
            print("3. Check service logs for error details")
            print("4. Verify dependencies are installed")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
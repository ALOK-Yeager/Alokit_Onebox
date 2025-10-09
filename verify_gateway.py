#!/usr/bin/env python3
"""
API Gateway Verification Script

This script tests the API Gateway functionality and verifies that it's
properly integrated with the Onebox Aggregator project.
"""

import requests
import time
import json
from typing import Dict, Any, Optional

class GatewayTester:
    def __init__(self, gateway_url: str = "http://localhost:3001"):
        self.gateway_url = gateway_url
        self.results = []

    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict[Any, Any]] = None, expected_status: Optional[int] = None) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        url = f"{self.gateway_url}{endpoint}"
        
        print(f"Testing {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_type": response.headers.get("content-type", ""),
                "success": True
            }
            
            # Try to parse JSON response
            try:
                result["response"] = response.json()
            except json.JSONDecodeError:
                result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Check expected status if provided
            if expected_status and response.status_code != expected_status:
                result["success"] = False
                result["expected_status"] = expected_status
                
            return result
            
        except requests.exceptions.ConnectionError:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "connection_error",
                "success": False,
                "message": "Could not connect to gateway"
            }
        except requests.exceptions.Timeout:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "timeout",
                "success": False,
                "message": "Request timed out"
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "error",
                "success": False,
                "message": str(e)
            }

    def run_basic_tests(self):
        """Run basic gateway functionality tests"""
        print("🧪 Running API Gateway Basic Tests")
        print("=" * 50)
        
        tests = [
            # Basic gateway endpoints
            {"endpoint": "/", "description": "Gateway root endpoint"},
            {"endpoint": "/health", "description": "Gateway health check"},
            {"endpoint": "/docs", "description": "API documentation"},
            
            # Search endpoints (will fail if services are down, but should return proper errors)
            {"endpoint": "/api/search?q=test", "description": "Search routing test"},
            {"endpoint": "/api/vector-search?q=test", "description": "Vector search routing test"},
            
            # Email endpoints
            {"endpoint": "/api/emails/test-id", "description": "Email retrieval routing test"},
            
            # Stats endpoint
            {"endpoint": "/api/stats", "description": "Stats routing test"},
        ]
        
        for test in tests:
            print(f"\n🔍 {test['description']}")
            result = self.test_endpoint(test["endpoint"])
            self.results.append(result)
            
            if result["success"]:
                print(f"   ✅ Status: {result['status_code']} ({result['response_time_ms']:.1f}ms)")
            else:
                print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
            
            time.sleep(0.5)  # Brief pause between tests

    def run_service_dependency_tests(self):
        """Test how gateway handles missing backend services"""
        print("\n🔗 Testing Service Dependency Handling")
        print("=" * 50)
        
        # These should return 503 Service Unavailable if backend services are down
        dependency_tests = [
            {"endpoint": "/api/search?q=test", "expected_status": 503},
            {"endpoint": "/api/vector-search?q=test", "expected_status": 503},
            {"endpoint": "/api/emails/test-id", "expected_status": 503},
        ]
        
        for test in dependency_tests:
            print(f"\n🔍 Testing service dependency: {test['endpoint']}")
            result = self.test_endpoint(test["endpoint"], expected_status=test.get("expected_status"))
            self.results.append(result)
            
            if result["success"] and result["status_code"] == 503:
                print(f"   ✅ Correctly returns 503 when service unavailable")
            elif result["success"] and result["status_code"] == 200:
                print(f"   ✅ Service is available and responding")
            else:
                print(f"   ⚠️  Unexpected response: {result['status_code']}")

    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['endpoint']}: {test.get('message', 'Unknown error')}")
        
        # Show service status
        health_test = next((r for r in self.results if r["endpoint"] == "/health"), None)
        if health_test and health_test["success"]:
            response = health_test.get("response", {})
            if isinstance(response, dict):
                services = response.get("services", {})
                print(f"\n🔗 Backend Service Status:")
                print(f"   • API Server: {'✅ Available' if services.get('api_server') else '❌ Unavailable'}")
                print(f"   • VectorDB Service: {'✅ Available' if services.get('vectordb_service') else '❌ Unavailable'}")

    def check_gateway_status(self):
        """Quick check if gateway is running"""
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

def main():
    print("🚀 Onebox Aggregator API Gateway Verification")
    print("=" * 60)
    
    gateway_url = "http://localhost:3001"
    tester = GatewayTester(gateway_url)
    
    # Check if gateway is running
    print(f"🔍 Checking if gateway is running at {gateway_url}...")
    
    if not tester.check_gateway_status():
        print("❌ Gateway is not running!")
        print("\nTo start the gateway, run:")
        print("   python api_gateway_onebox.py")
        print("\nOr use the startup script:")
        print("   .\\start-services.ps1")
        return
    
    print("✅ Gateway is running!")
    
    # Run tests
    tester.run_basic_tests()
    tester.run_service_dependency_tests()
    tester.print_summary()
    
    print(f"\n🌐 Gateway URLs:")
    print(f"   • Main: {gateway_url}")
    print(f"   • Docs: {gateway_url}/docs")
    print(f"   • Health: {gateway_url}/health")
    
    print(f"\n📝 Next Steps:")
    print(f"   1. Start backend services: python api_server.py & python vectordb_service.py")
    print(f"   2. Run integration tests with all services running")
    print(f"   3. Check logs in ./logs/ directory for detailed output")

if __name__ == "__main__":
    main()
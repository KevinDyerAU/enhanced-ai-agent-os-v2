#!/usr/bin/env python3
"""
Comprehensive test runner for Universal Airlock System
Executes all 8 phases of testing as specified in the testing script
"""

import asyncio
import subprocess
import sys
import time
import json
import aiohttp
from datetime import datetime
from typing import Dict, Any, List

class TestRunner:
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def check_service_health(self, service_url: str, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/health", timeout=5) as response:
                    if response.status == 200:
                        self.log(f"✅ {service_name} is healthy")
                        return True
                    else:
                        self.log(f"❌ {service_name} health check failed: HTTP {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ {service_name} health check failed: {e}", "ERROR")
            return False
    
    async def phase_1_environment_setup(self) -> Dict[str, Any]:
        """Phase 1: Environment Setup and Basic Validation"""
        self.log("=== PHASE 1: Environment Setup and Basic Validation ===")
        
        results = {
            "phase": "Environment Setup",
            "tests": {},
            "overall_success": True
        }
        
        self.log("Checking Docker Compose services...")
        try:
            result = subprocess.run(["docker-compose", "ps"], 
                                  capture_output=True, text=True, cwd="/home/ubuntu/enhanced-ai-agent-os-v2")
            if result.returncode == 0:
                self.log("✅ Docker Compose services are running")
                results["tests"]["docker_compose"] = True
            else:
                self.log(f"❌ Docker Compose check failed: {result.stderr}", "ERROR")
                results["tests"]["docker_compose"] = False
                results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Docker Compose check failed: {e}", "ERROR")
            results["tests"]["docker_compose"] = False
            results["overall_success"] = False
        
        services_to_check = [
            ("http://localhost:8007", "Airlock System"),
            ("http://localhost:5173", "Frontend"),
        ]
        
        for service_url, service_name in services_to_check:
            is_healthy = await self.check_service_health(service_url, service_name)
            results["tests"][f"{service_name.lower().replace(' ', '_')}_health"] = is_healthy
            if not is_healthy:
                results["overall_success"] = False
        
        self.log("Testing database connectivity...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8007/api/v1/airlock/items", timeout=10) as response:
                    if response.status in [200, 404]:  # 404 is OK if no items exist yet
                        self.log("✅ Database connectivity verified")
                        results["tests"]["database_connectivity"] = True
                    else:
                        self.log(f"❌ Database connectivity test failed: HTTP {response.status}", "ERROR")
                        results["tests"]["database_connectivity"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Database connectivity test failed: {e}", "ERROR")
            results["tests"]["database_connectivity"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_2_api_functionality(self) -> Dict[str, Any]:
        """Phase 2: API Functionality Testing"""
        self.log("=== PHASE 2: API Functionality Testing ===")
        
        results = {
            "phase": "API Functionality",
            "tests": {},
            "overall_success": True
        }
        
        self.log("Testing content submission...")
        try:
            test_payload = {
                "content_type": "training_validation",
                "source_service": "test_runner",
                "source_id": "test_001",
                "title": "Test Training Unit Validation",
                "description": "Testing airlock submission workflow",
                "content": {
                    "unit_code": "BSBWHS311",
                    "unit_title": "Assist with maintaining workplace safety",
                    "validation_results": {
                        "overall_score": 85,
                        "assessment_conditions": {"score": 90, "status": "pass"},
                        "performance_evidence": {"score": 80, "status": "pass"},
                        "knowledge_evidence": {"score": 85, "status": "pass"},
                        "foundation_skills": {"score": 88, "status": "pass"}
                    }
                },
                "metadata": {
                    "confidence_score": 0.85,
                    "ai_agent_version": "v2.1.0",
                    "processing_time": 45.2
                },
                "priority": "medium"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:8007/api/v1/airlock/items", 
                                      json=test_payload) as response:
                    if response.status == 201:
                        response_data = await response.json()
                        airlock_id = response_data.get("id")
                        self.log(f"✅ Content submission successful, ID: {airlock_id}")
                        results["tests"]["content_submission"] = True
                        results["airlock_id"] = airlock_id
                    else:
                        error_text = await response.text()
                        self.log(f"❌ Content submission failed: HTTP {response.status} - {error_text}", "ERROR")
                        results["tests"]["content_submission"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Content submission test failed: {e}", "ERROR")
            results["tests"]["content_submission"] = False
            results["overall_success"] = False
        
        if results["tests"].get("content_submission") and "airlock_id" in results:
            self.log("Testing content retrieval...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:8007/api/v1/airlock/items/{results['airlock_id']}") as response:
                        if response.status == 200:
                            self.log("✅ Content retrieval successful")
                            results["tests"]["content_retrieval"] = True
                        else:
                            self.log(f"❌ Content retrieval failed: HTTP {response.status}", "ERROR")
                            results["tests"]["content_retrieval"] = False
                            results["overall_success"] = False
            except Exception as e:
                self.log(f"❌ Content retrieval test failed: {e}", "ERROR")
                results["tests"]["content_retrieval"] = False
                results["overall_success"] = False
        
        self.log("Testing item listing...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8007/api/v1/airlock/items") as response:
                    if response.status == 200:
                        items = await response.json()
                        self.log(f"✅ Item listing successful, found {len(items)} items")
                        results["tests"]["item_listing"] = True
                    else:
                        self.log(f"❌ Item listing failed: HTTP {response.status}", "ERROR")
                        results["tests"]["item_listing"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Item listing test failed: {e}", "ERROR")
            results["tests"]["item_listing"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_3_websocket_testing(self) -> Dict[str, Any]:
        """Phase 3: WebSocket Real-time Communication Testing"""
        self.log("=== PHASE 3: WebSocket Real-time Communication Testing ===")
        
        results = {
            "phase": "WebSocket Communication",
            "tests": {},
            "overall_success": True
        }
        
        try:
            from test_websocket import run_websocket_tests
            websocket_success = await run_websocket_tests()
            results["tests"]["websocket_functionality"] = websocket_success
            if not websocket_success:
                results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ WebSocket tests failed: {e}", "ERROR")
            results["tests"]["websocket_functionality"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_4_frontend_testing(self) -> Dict[str, Any]:
        """Phase 4: Frontend Integration Testing"""
        self.log("=== PHASE 4: Frontend Integration Testing ===")
        
        results = {
            "phase": "Frontend Integration",
            "tests": {},
            "overall_success": True
        }
        
        self.log("Testing frontend accessibility...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:5173") as response:
                    if response.status == 200:
                        content = await response.text()
                        if "Universal Airlock" in content or "react" in content.lower():
                            self.log("✅ Frontend is accessible and contains expected content")
                            results["tests"]["frontend_accessibility"] = True
                        else:
                            self.log("❌ Frontend accessible but missing expected content", "ERROR")
                            results["tests"]["frontend_accessibility"] = False
                            results["overall_success"] = False
                    else:
                        self.log(f"❌ Frontend accessibility test failed: HTTP {response.status}", "ERROR")
                        results["tests"]["frontend_accessibility"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Frontend accessibility test failed: {e}", "ERROR")
            results["tests"]["frontend_accessibility"] = False
            results["overall_success"] = False
        
        self.log("Testing API connectivity...")
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Origin": "http://localhost:5173",
                    "Referer": "http://localhost:5173/"
                }
                async with session.get("http://localhost:8007/api/v1/airlock/items", 
                                     headers=headers) as response:
                    if response.status == 200:
                        self.log("✅ API connectivity from frontend perspective successful")
                        results["tests"]["api_connectivity"] = True
                    else:
                        self.log(f"❌ API connectivity test failed: HTTP {response.status}", "ERROR")
                        results["tests"]["api_connectivity"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ API connectivity test failed: {e}", "ERROR")
            results["tests"]["api_connectivity"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_5_integration_testing(self) -> Dict[str, Any]:
        """Phase 5: Integration Testing with Existing Services"""
        self.log("=== PHASE 5: Integration Testing with Existing Services ===")
        
        results = {
            "phase": "Service Integration",
            "tests": {},
            "overall_success": True
        }
        
        services_to_test = [
            ("http://localhost:8033", "Training Validation Service"),
            ("http://localhost:8001", "Ideation Agent"),
            ("http://localhost:8006", "Audit Service")
        ]
        
        for service_url, service_name in services_to_test:
            self.log(f"Testing integration with {service_name}...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{service_url}/health", timeout=5) as response:
                        if response.status == 200:
                            self.log(f"✅ {service_name} is available for integration")
                            results["tests"][f"{service_name.lower().replace(' ', '_')}_integration"] = True
                        else:
                            self.log(f"⚠️ {service_name} not available (HTTP {response.status})")
                            results["tests"][f"{service_name.lower().replace(' ', '_')}_integration"] = False
            except Exception as e:
                self.log(f"⚠️ {service_name} not available: {e}")
                results["tests"][f"{service_name.lower().replace(' ', '_')}_integration"] = False
        
        
        return results
    
    async def phase_6_performance_testing(self) -> Dict[str, Any]:
        """Phase 6: Performance and Load Testing"""
        self.log("=== PHASE 6: Performance and Load Testing ===")
        
        results = {
            "phase": "Performance Testing",
            "tests": {},
            "overall_success": True
        }
        
        try:
            from test_load import run_load_tests
            load_test_results = await run_load_tests()
            
            all_passed = all(result.get("success", False) for result in load_test_results.values())
            results["tests"]["load_testing"] = all_passed
            results["load_test_details"] = load_test_results
            
            if not all_passed:
                results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Load tests failed: {e}", "ERROR")
            results["tests"]["load_testing"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_7_security_testing(self) -> Dict[str, Any]:
        """Phase 7: Security and Error Handling Testing"""
        self.log("=== PHASE 7: Security and Error Handling Testing ===")
        
        results = {
            "phase": "Security Testing",
            "tests": {},
            "overall_success": True
        }
        
        try:
            from test_security import run_security_tests
            security_success = await run_security_tests()
            results["tests"]["security_testing"] = security_success
            if not security_success:
                results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ Security tests failed: {e}", "ERROR")
            results["tests"]["security_testing"] = False
            results["overall_success"] = False
        
        return results
    
    async def phase_8_documentation_review(self) -> Dict[str, Any]:
        """Phase 8: Documentation and Code Quality Review"""
        self.log("=== PHASE 8: Documentation and Code Quality Review ===")
        
        results = {
            "phase": "Documentation Review",
            "tests": {},
            "overall_success": True
        }
        
        self.log("Checking API documentation...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8007/docs") as response:
                    if response.status == 200:
                        self.log("✅ API documentation is accessible")
                        results["tests"]["api_documentation"] = True
                    else:
                        self.log(f"❌ API documentation not accessible: HTTP {response.status}", "ERROR")
                        results["tests"]["api_documentation"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ API documentation check failed: {e}", "ERROR")
            results["tests"]["api_documentation"] = False
            results["overall_success"] = False
        
        self.log("Checking OpenAPI schema...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8007/openapi.json") as response:
                    if response.status == 200:
                        schema = await response.json()
                        if "paths" in schema and len(schema["paths"]) > 0:
                            self.log(f"✅ OpenAPI schema is complete with {len(schema['paths'])} endpoints")
                            results["tests"]["openapi_schema"] = True
                        else:
                            self.log("❌ OpenAPI schema is incomplete", "ERROR")
                            results["tests"]["openapi_schema"] = False
                            results["overall_success"] = False
                    else:
                        self.log(f"❌ OpenAPI schema not accessible: HTTP {response.status}", "ERROR")
                        results["tests"]["openapi_schema"] = False
                        results["overall_success"] = False
        except Exception as e:
            self.log(f"❌ OpenAPI schema check failed: {e}", "ERROR")
            results["tests"]["openapi_schema"] = False
            results["overall_success"] = False
        
        return results
    
    async def run_all_phases(self) -> Dict[str, Any]:
        """Run all testing phases"""
        self.start_time = datetime.now()
        self.log("Starting Universal Airlock System Comprehensive Testing")
        
        phases = [
            self.phase_1_environment_setup,
            self.phase_2_api_functionality,
            self.phase_3_websocket_testing,
            self.phase_4_frontend_testing,
            self.phase_5_integration_testing,
            self.phase_6_performance_testing,
            self.phase_7_security_testing,
            self.phase_8_documentation_review
        ]
        
        for i, phase_func in enumerate(phases, 1):
            self.log(f"Starting Phase {i}...")
            try:
                phase_result = await phase_func()
                self.test_results[f"phase_{i}"] = phase_result
                
                if phase_result["overall_success"]:
                    self.log(f"✅ Phase {i} PASSED")
                else:
                    self.log(f"❌ Phase {i} FAILED")
            except Exception as e:
                self.log(f"❌ Phase {i} FAILED with exception: {e}", "ERROR")
                self.test_results[f"phase_{i}"] = {
                    "phase": f"Phase {i}",
                    "overall_success": False,
                    "error": str(e)
                }
            
            self.log("")  # Add spacing between phases
        
        self.end_time = datetime.now()
        return self.generate_final_report()
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_phases = len(self.test_results)
        passed_phases = sum(1 for result in self.test_results.values() 
                           if result.get("overall_success", False))
        
        total_tests = 0
        passed_tests = 0
        
        for phase_result in self.test_results.values():
            if "tests" in phase_result:
                for test_name, test_result in phase_result["tests"].items():
                    total_tests += 1
                    if test_result:
                        passed_tests += 1
        
        execution_time = (self.end_time - self.start_time).total_seconds()
        
        report = {
            "executive_summary": {
                "total_phases": total_phases,
                "passed_phases": passed_phases,
                "phase_success_rate": (passed_phases / total_phases * 100) if total_phases > 0 else 0,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "test_success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "execution_time_seconds": execution_time,
                "overall_status": "PASSED" if passed_phases == total_phases else "FAILED"
            },
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations(),
            "deployment_readiness": self.assess_deployment_readiness()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for phase_name, phase_result in self.test_results.items():
            if not phase_result.get("overall_success", True):
                if "environment" in phase_result.get("phase", "").lower():
                    recommendations.append("Review Docker Compose configuration and service dependencies")
                elif "security" in phase_result.get("phase", "").lower():
                    recommendations.append("Address security vulnerabilities before production deployment")
                elif "performance" in phase_result.get("phase", "").lower():
                    recommendations.append("Optimize performance bottlenecks identified in load testing")
                elif "websocket" in phase_result.get("phase", "").lower():
                    recommendations.append("Review WebSocket implementation for real-time communication issues")
        
        if not recommendations:
            recommendations.append("All tests passed - system appears ready for production deployment")
        
        return recommendations
    
    def assess_deployment_readiness(self) -> Dict[str, Any]:
        """Assess if the system is ready for deployment"""
        critical_phases = ["phase_1", "phase_2", "phase_7"]  # Environment, API, Security
        critical_passed = all(self.test_results.get(phase, {}).get("overall_success", False) 
                             for phase in critical_phases)
        
        total_success_rate = self.test_results and len([r for r in self.test_results.values() 
                                                       if r.get("overall_success", False)]) / len(self.test_results) * 100
        
        if critical_passed and total_success_rate >= 80:
            readiness = "READY"
        elif critical_passed:
            readiness = "READY_WITH_WARNINGS"
        else:
            readiness = "NOT_READY"
        
        return {
            "status": readiness,
            "critical_systems_passed": critical_passed,
            "overall_success_rate": total_success_rate,
            "blocking_issues": [
                phase_result.get("phase", phase_name) 
                for phase_name, phase_result in self.test_results.items()
                if not phase_result.get("overall_success", True) and phase_name in critical_phases
            ]
        }

async def main():
    """Main test execution function"""
    runner = TestRunner()
    
    try:
        final_report = await runner.run_all_phases()
        
        print("\n" + "="*80)
        print("UNIVERSAL AIRLOCK SYSTEM - COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        summary = final_report["executive_summary"]
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Phases Passed: {summary['passed_phases']}/{summary['total_phases']} ({summary['phase_success_rate']:.1f}%)")
        print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['test_success_rate']:.1f}%)")
        print(f"Execution Time: {summary['execution_time_seconds']:.1f} seconds")
        
        print(f"\nDeployment Readiness: {final_report['deployment_readiness']['status']}")
        
        if final_report["recommendations"]:
            print("\nRecommendations:")
            for rec in final_report["recommendations"]:
                print(f"  - {rec}")
        
        with open("/home/ubuntu/enhanced-ai-agent-os-v2/test_report.json", "w") as f:
            json.dump(final_report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: /home/ubuntu/enhanced-ai-agent-os-v2/test_report.json")
        
        if summary["overall_status"] == "PASSED":
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

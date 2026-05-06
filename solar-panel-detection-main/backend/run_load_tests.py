"""
Run Load Tests and Analyze Results
Task 19.3 - Run load tests

This script:
1. Runs Locust load tests
2. Analyzes results
3. Verifies performance targets are met
4. Identifies bottlenecks

Usage:
    python run_load_tests.py [--host http://localhost:8080] [--users 100] [--duration 60]
"""

import subprocess
import argparse
import time
import json
import os
from datetime import datetime
from typing import Dict, List


class LoadTestRunner:
    """
    Load test runner and analyzer
    
    Runs Locust load tests and analyzes results to verify:
    - Response time p95 < 600ms
    - Cache hit rate > 60%
    - No errors under load
    - Identifies bottlenecks
    """
    
    def __init__(self, host: str, users: int, duration: int):
        self.host = host
        self.users = users
        self.duration = duration
        self.results_dir = "load_test_results"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_locust_test(self, user_class: str = "SolarPotentialUser") -> Dict:
        """
        Run Locust load test
        
        Args:
            user_class: Locust user class to use
            
        Returns:
            Test results dictionary
        """
        print(f"\n{'='*80}")
        print(f"RUNNING LOAD TEST")
        print(f"{'='*80}")
        print(f"Host: {self.host}")
        print(f"Users: {self.users}")
        print(f"Duration: {self.duration}s")
        print(f"User class: {user_class}")
        print(f"{'='*80}\n")
        
        # Output files
        csv_prefix = f"{self.results_dir}/load_test_{self.timestamp}"
        html_file = f"{self.results_dir}/load_test_{self.timestamp}.html"
        
        # Build Locust command
        cmd = [
            "locust",
            "-f", "tests/locustfile.py",
            "--host", self.host,
            "--users", str(self.users),
            "--spawn-rate", str(min(10, self.users)),  # Spawn 10 users/sec
            "--run-time", f"{self.duration}s",
            "--headless",  # Run without web UI
            "--csv", csv_prefix,
            "--html", html_file,
            user_class
        ]
        
        print(f"Running command: {' '.join(cmd)}\n")
        
        try:
            # Run Locust
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd="solar-panel-detection-main/backend"
            )
            duration = time.time() - start_time
            
            print(f"\n{'='*80}")
            print(f"LOAD TEST COMPLETED")
            print(f"{'='*80}")
            print(f"Duration: {duration:.2f}s")
            print(f"Exit code: {result.returncode}")
            
            # Print output
            if result.stdout:
                print(f"\nOutput:")
                print(result.stdout)
            
            if result.stderr:
                print(f"\nErrors:")
                print(result.stderr)
            
            # Parse results
            results = self.parse_locust_results(csv_prefix)
            results["html_report"] = html_file
            results["exit_code"] = result.returncode
            results["duration_seconds"] = duration
            
            return results
            
        except FileNotFoundError:
            print(f"\n✗ Error: Locust not found. Install with: pip install locust")
            return {"error": "Locust not installed"}
        except Exception as e:
            print(f"\n✗ Error running load test: {str(e)}")
            return {"error": str(e)}
    
    def parse_locust_results(self, csv_prefix: str) -> Dict:
        """
        Parse Locust CSV results
        
        Args:
            csv_prefix: Prefix for CSV files
            
        Returns:
            Parsed results dictionary
        """
        results = {
            "endpoints": {},
            "summary": {}
        }
        
        # Parse stats CSV
        stats_file = f"{csv_prefix}_stats.csv"
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                lines = f.readlines()
                
                # Skip header
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    if len(parts) >= 10 and parts[0] != "Aggregated":
                        endpoint_name = parts[1].strip('"')
                        
                        results["endpoints"][endpoint_name] = {
                            "method": parts[0].strip('"'),
                            "requests": int(parts[2]) if parts[2] else 0,
                            "failures": int(parts[3]) if parts[3] else 0,
                            "median_ms": float(parts[4]) if parts[4] else 0,
                            "average_ms": float(parts[5]) if parts[5] else 0,
                            "min_ms": float(parts[6]) if parts[6] else 0,
                            "max_ms": float(parts[7]) if parts[7] else 0,
                            "p90_ms": float(parts[8]) if parts[8] else 0,
                            "p95_ms": float(parts[9]) if parts[9] else 0,
                            "p99_ms": float(parts[10]) if parts[10] and len(parts) > 10 else 0,
                            "rps": float(parts[11]) if parts[11] and len(parts) > 11 else 0
                        }
                    elif parts[0] == "Aggregated":
                        # Summary row
                        results["summary"] = {
                            "total_requests": int(parts[2]) if parts[2] else 0,
                            "total_failures": int(parts[3]) if parts[3] else 0,
                            "median_ms": float(parts[4]) if parts[4] else 0,
                            "average_ms": float(parts[5]) if parts[5] else 0,
                            "min_ms": float(parts[6]) if parts[6] else 0,
                            "max_ms": float(parts[7]) if parts[7] else 0,
                            "p90_ms": float(parts[8]) if parts[8] else 0,
                            "p95_ms": float(parts[9]) if parts[9] else 0,
                            "p99_ms": float(parts[10]) if parts[10] and len(parts) > 10 else 0,
                            "rps": float(parts[11]) if parts[11] and len(parts) > 11 else 0
                        }
        
        return results
    
    def analyze_results(self, results: Dict) -> Dict:
        """
        Analyze load test results
        
        Checks:
        - Performance targets (p95 < 600ms)
        - Error rates
        - Bottlenecks
        
        Returns:
            Analysis results
        """
        print(f"\n{'='*80}")
        print(f"ANALYZING RESULTS")
        print(f"{'='*80}")
        
        analysis = {
            "performance_target_met": False,
            "error_rate_acceptable": False,
            "bottlenecks": [],
            "recommendations": []
        }
        
        if "error" in results:
            print(f"✗ Load test failed: {results['error']}")
            return analysis
        
        # Check summary statistics
        summary = results.get("summary", {})
        
        if not summary:
            print(f"⚠ No summary statistics available")
            return analysis
        
        print(f"\nOverall Statistics:")
        print(f"  Total requests: {summary.get('total_requests', 0):,}")
        print(f"  Total failures: {summary.get('total_failures', 0):,}")
        print(f"  Requests/sec: {summary.get('rps', 0):.2f}")
        print(f"  Average response time: {summary.get('average_ms', 0):.2f}ms")
        print(f"  Median response time: {summary.get('median_ms', 0):.2f}ms")
        print(f"  p90 response time: {summary.get('p90_ms', 0):.2f}ms")
        print(f"  p95 response time: {summary.get('p95_ms', 0):.2f}ms")
        print(f"  p99 response time: {summary.get('p99_ms', 0):.2f}ms")
        print(f"  Max response time: {summary.get('max_ms', 0):.2f}ms")
        
        # Check performance target (p95 < 600ms)
        p95 = summary.get('p95_ms', 0)
        target_p95 = 600
        
        print(f"\n{'='*80}")
        print(f"PERFORMANCE TARGET CHECK")
        print(f"{'='*80}")
        print(f"Target: p95 < {target_p95}ms")
        print(f"Actual: p95 = {p95:.2f}ms")
        
        if p95 < target_p95:
            print(f"✓ PASS - Performance target met")
            analysis["performance_target_met"] = True
        else:
            print(f"✗ FAIL - Performance target not met")
            analysis["performance_target_met"] = False
            analysis["recommendations"].append(
                f"Optimize slow endpoints to reduce p95 from {p95:.2f}ms to < {target_p95}ms"
            )
        
        # Check error rate
        total_requests = summary.get('total_requests', 0)
        total_failures = summary.get('total_failures', 0)
        error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"ERROR RATE CHECK")
        print(f"{'='*80}")
        print(f"Total failures: {total_failures:,}")
        print(f"Error rate: {error_rate:.2f}%")
        
        target_error_rate = 0.1
        if error_rate <= target_error_rate:
            print(f"✓ PASS - Error rate acceptable (< {target_error_rate}%)")
            analysis["error_rate_acceptable"] = True
        else:
            print(f"✗ FAIL - Error rate too high (> {target_error_rate}%)")
            analysis["error_rate_acceptable"] = False
            analysis["recommendations"].append(
                f"Investigate and fix errors causing {error_rate:.2f}% failure rate"
            )
        
        # Identify bottlenecks (endpoints with p95 > 600ms)
        print(f"\n{'='*80}")
        print(f"BOTTLENECK ANALYSIS")
        print(f"{'='*80}")
        
        endpoints = results.get("endpoints", {})
        slow_endpoints = []
        
        for endpoint_name, stats in endpoints.items():
            p95_endpoint = stats.get('p95_ms', 0)
            if p95_endpoint > target_p95:
                slow_endpoints.append({
                    "endpoint": endpoint_name,
                    "p95_ms": p95_endpoint,
                    "requests": stats.get('requests', 0),
                    "failures": stats.get('failures', 0)
                })
        
        if slow_endpoints:
            print(f"Found {len(slow_endpoints)} slow endpoints:")
            for endpoint in sorted(slow_endpoints, key=lambda x: x['p95_ms'], reverse=True):
                print(f"  ⚠ {endpoint['endpoint']}")
                print(f"     p95: {endpoint['p95_ms']:.2f}ms")
                print(f"     requests: {endpoint['requests']:,}")
                print(f"     failures: {endpoint['failures']:,}")
            
            analysis["bottlenecks"] = slow_endpoints
            analysis["recommendations"].append(
                f"Optimize {len(slow_endpoints)} slow endpoints identified above"
            )
        else:
            print(f"✓ No bottlenecks found - all endpoints meet performance target")
        
        # Per-endpoint analysis
        print(f"\n{'='*80}")
        print(f"PER-ENDPOINT STATISTICS")
        print(f"{'='*80}")
        print(f"{'Endpoint':<50} {'Requests':<12} {'p95 (ms)':<12} {'Status':<10}")
        print(f"{'-'*80}")
        
        for endpoint_name, stats in sorted(endpoints.items(), key=lambda x: x[1].get('p95_ms', 0), reverse=True):
            p95_endpoint = stats.get('p95_ms', 0)
            requests = stats.get('requests', 0)
            status = "✓" if p95_endpoint < target_p95 else "⚠"
            
            print(f"{endpoint_name:<50} {requests:<12,} {p95_endpoint:<12.2f} {status:<10}")
        
        return analysis
    
    def generate_report(self, results: Dict, analysis: Dict):
        """
        Generate comprehensive test report
        """
        report_file = f"{self.results_dir}/load_test_report_{self.timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("LOAD TEST REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write(f"Host: {self.host}\n")
            f.write(f"Users: {self.users}\n")
            f.write(f"Duration: {self.duration}s\n")
            f.write("="*80 + "\n\n")
            
            # Summary
            summary = results.get("summary", {})
            f.write("SUMMARY\n")
            f.write("-"*80 + "\n")
            f.write(f"Total requests: {summary.get('total_requests', 0):,}\n")
            f.write(f"Total failures: {summary.get('total_failures', 0):,}\n")
            f.write(f"Requests/sec: {summary.get('rps', 0):.2f}\n")
            f.write(f"p95 response time: {summary.get('p95_ms', 0):.2f}ms\n")
            f.write(f"p99 response time: {summary.get('p99_ms', 0):.2f}ms\n\n")
            
            # Performance target
            f.write("PERFORMANCE TARGET\n")
            f.write("-"*80 + "\n")
            f.write(f"Target: p95 < 600ms\n")
            f.write(f"Actual: p95 = {summary.get('p95_ms', 0):.2f}ms\n")
            f.write(f"Status: {'PASS' if analysis['performance_target_met'] else 'FAIL'}\n\n")
            
            # Bottlenecks
            if analysis['bottlenecks']:
                f.write("BOTTLENECKS\n")
                f.write("-"*80 + "\n")
                for bottleneck in analysis['bottlenecks']:
                    f.write(f"- {bottleneck['endpoint']}: {bottleneck['p95_ms']:.2f}ms\n")
                f.write("\n")
            
            # Recommendations
            if analysis['recommendations']:
                f.write("RECOMMENDATIONS\n")
                f.write("-"*80 + "\n")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")
        
        print(f"\n✓ Report saved to: {report_file}")
        return report_file
    
    def run_full_test_suite(self):
        """
        Run complete load test suite
        """
        print(f"\n{'='*80}")
        print(f"LOAD TEST SUITE")
        print(f"{'='*80}")
        print(f"Starting load tests at {datetime.now().isoformat()}")
        print(f"{'='*80}\n")
        
        # Run main load test
        results = self.run_locust_test()
        
        # Analyze results
        analysis = self.analyze_results(results)
        
        # Generate report
        report_file = self.generate_report(results, analysis)
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"FINAL SUMMARY")
        print(f"{'='*80}")
        
        if analysis["performance_target_met"] and analysis["error_rate_acceptable"]:
            print(f"✓ All tests passed!")
            print(f"  - Performance target met (p95 < 600ms)")
            print(f"  - Error rate acceptable (< 0.1%)")
        else:
            print(f"⚠ Some tests failed:")
            if not analysis["performance_target_met"]:
                print(f"  ✗ Performance target not met")
            if not analysis["error_rate_acceptable"]:
                print(f"  ✗ Error rate too high")
        
        if analysis["bottlenecks"]:
            print(f"\n⚠ {len(analysis['bottlenecks'])} bottlenecks identified")
        
        if analysis["recommendations"]:
            print(f"\nRecommendations:")
            for i, rec in enumerate(analysis["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n{'='*80}")
        print(f"Report: {report_file}")
        if "html_report" in results:
            print(f"HTML Report: {results['html_report']}")
        print(f"{'='*80}\n")
        
        return analysis["performance_target_met"] and analysis["error_rate_acceptable"]


def main():
    parser = argparse.ArgumentParser(
        description="Run load tests for Solar Potential API"
    )
    parser.add_argument(
        '--host',
        default='http://localhost:8080',
        help="API host URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        '--users',
        type=int,
        default=100,
        help="Number of concurrent users (default: 100)"
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = LoadTestRunner(args.host, args.users, args.duration)
    success = runner.run_full_test_suite()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()

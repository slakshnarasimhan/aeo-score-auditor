#!/usr/bin/env python3
"""
AEO Score Benchmark Suite
Tests scoring system against known-good sites to identify calibration issues
"""
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any
import httpx
from pathlib import Path
from loguru import logger

# Configuration
API_URL = "http://localhost:8000"
BENCHMARK_FILE = "benchmark_sites.json"
RESULTS_DIR = "benchmark_results"


class BenchmarkRunner:
    """Runs benchmark tests against multiple sites and analyzes results"""
    
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        self.results = []
        self.benchmark_data = None
        
    def load_benchmark_sites(self, filepath: str = BENCHMARK_FILE) -> Dict:
        """Load benchmark site definitions"""
        logger.info(f"Loading benchmark sites from {filepath}")
        with open(filepath, 'r') as f:
            self.benchmark_data = json.load(f)
        
        total_sites = sum(
            len(cat['sites']) 
            for cat in self.benchmark_data['categories'].values()
        )
        logger.info(f"Loaded {total_sites} benchmark sites across {len(self.benchmark_data['categories'])} categories")
        return self.benchmark_data
    
    async def audit_site(self, url: str, retry: int = 2) -> Dict[str, Any]:
        """Run audit on a single site"""
        logger.info(f"Auditing: {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(retry + 1):
                try:
                    response = await client.post(
                        f"{self.api_url}/api/v1/audit/page",
                        json={"url": url}
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        # Handle nested result structure
                        result = response_data.get('result', response_data)
                        score = result.get('overall_score', 0)
                        logger.success(f"✓ Audited {url}: {score}/100")
                        return result
                    else:
                        logger.warning(f"Attempt {attempt + 1} failed: {response.status_code}")
                        if attempt < retry:
                            await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Error auditing {url}: {e}")
                    if attempt < retry:
                        await asyncio.sleep(2)
        
        logger.error(f"✗ Failed to audit {url} after {retry + 1} attempts")
        return None
    
    async def run_benchmark_category(self, category_name: str, category_data: Dict) -> List[Dict]:
        """Run benchmarks for a specific category"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing Category: {category_name.upper()}")
        logger.info(f"Description: {category_data['description']}")
        logger.info(f"Expected Range: {category_data['expected_range'][0]}-{category_data['expected_range'][1]}/100")
        logger.info(f"{'='*60}\n")
        
        category_results = []
        
        for site in category_data['sites']:
            logger.info(f"Testing: {site['name']}")
            logger.info(f"  URL: {site['url']}")
            logger.info(f"  Expected: {site['expected_score']}/100")
            
            # Run audit
            audit_result = await self.audit_site(site['url'])
            
            if audit_result:
                actual_score = audit_result.get('overall_score', 0)
                expected_score = site['expected_score']
                difference = actual_score - expected_score
                
                result = {
                    'category': category_name,
                    'name': site['name'],
                    'url': site['url'],
                    'expected_score': expected_score,
                    'actual_score': actual_score,
                    'difference': difference,
                    'percentage_error': abs(difference / expected_score * 100) if expected_score > 0 else 0,
                    'expected_breakdown': site.get('category_expectations', {}),
                    'actual_breakdown': audit_result.get('breakdown', {}),
                    'grade': audit_result.get('grade', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Analyze category-level differences
                result['category_differences'] = self._analyze_category_differences(
                    site.get('category_expectations', {}),
                    audit_result.get('breakdown', {})
                )
                
                category_results.append(result)
                self.results.append(result)
                
                # Log summary
                status = "✓" if abs(difference) <= 10 else "✗"
                logger.info(f"  {status} Actual: {actual_score}/100 (Δ {difference:+.1f})")
                
            else:
                logger.error(f"  ✗ Failed to audit {site['name']}")
            
            # Delay between requests
            await asyncio.sleep(self.benchmark_data['test_config']['delay_between_requests'])
        
        return category_results
    
    def _analyze_category_differences(self, expected: Dict, actual: Dict) -> Dict:
        """Compare expected vs actual scores by category"""
        differences = {}
        
        for category, expected_score in expected.items():
            actual_data = actual.get(category, {})
            actual_score = actual_data.get('score', 0)
            diff = actual_score - expected_score
            
            differences[category] = {
                'expected': expected_score,
                'actual': actual_score,
                'difference': diff,
                'percentage_error': abs(diff / expected_score * 100) if expected_score > 0 else 0
            }
        
        return differences
    
    async def run_all_benchmarks(self) -> List[Dict]:
        """Run all benchmark tests"""
        logger.info("\n" + "="*80)
        logger.info("STARTING AEO BENCHMARK SUITE")
        logger.info("="*80)
        
        start_time = time.time()
        
        # Run tests for each category
        for category_name, category_data in self.benchmark_data['categories'].items():
            await self.run_benchmark_category(category_name, category_data)
        
        elapsed_time = time.time() - start_time
        logger.info(f"\n{'='*80}")
        logger.info(f"BENCHMARK COMPLETE - {len(self.results)} sites tested in {elapsed_time:.1f}s")
        logger.info(f"{'='*80}\n")
        
        return self.results
    
    def generate_report(self, output_file: str = None) -> Dict:
        """Generate comprehensive benchmark report"""
        if not self.results:
            logger.error("No results to report")
            return {}
        
        report = {
            'summary': self._generate_summary(),
            'category_analysis': self._analyze_by_category(),
            'scoring_issues': self._identify_scoring_issues(),
            'calibration_recommendations': self._generate_calibration_recommendations(),
            'detailed_results': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to file
        if output_file:
            Path(RESULTS_DIR).mkdir(exist_ok=True)
            filepath = Path(RESULTS_DIR) / output_file
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {filepath}")
        
        return report
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        total_sites = len(self.results)
        avg_expected = sum(r['expected_score'] for r in self.results) / total_sites
        avg_actual = sum(r['actual_score'] for r in self.results) / total_sites
        avg_difference = sum(r['difference'] for r in self.results) / total_sites
        avg_abs_difference = sum(abs(r['difference']) for r in self.results) / total_sites
        
        # Accuracy metrics
        within_5_points = sum(1 for r in self.results if abs(r['difference']) <= 5)
        within_10_points = sum(1 for r in self.results if abs(r['difference']) <= 10)
        within_15_points = sum(1 for r in self.results if abs(r['difference']) <= 15)
        
        return {
            'total_sites_tested': total_sites,
            'average_expected_score': round(avg_expected, 1),
            'average_actual_score': round(avg_actual, 1),
            'average_difference': round(avg_difference, 1),
            'average_absolute_error': round(avg_abs_difference, 1),
            'accuracy_metrics': {
                'within_5_points': {'count': within_5_points, 'percentage': round(within_5_points / total_sites * 100, 1)},
                'within_10_points': {'count': within_10_points, 'percentage': round(within_10_points / total_sites * 100, 1)},
                'within_15_points': {'count': within_15_points, 'percentage': round(within_15_points / total_sites * 100, 1)}
            },
            'systematic_bias': 'underscoring' if avg_difference < 0 else 'overscoring' if avg_difference > 0 else 'neutral'
        }
    
    def _analyze_by_category(self) -> Dict:
        """Analyze results grouped by benchmark category"""
        category_stats = {}
        
        for result in self.results:
            cat = result['category']
            if cat not in category_stats:
                category_stats[cat] = {
                    'sites': [],
                    'differences': [],
                    'expected_scores': [],
                    'actual_scores': []
                }
            
            category_stats[cat]['sites'].append(result['name'])
            category_stats[cat]['differences'].append(result['difference'])
            category_stats[cat]['expected_scores'].append(result['expected_score'])
            category_stats[cat]['actual_scores'].append(result['actual_score'])
        
        # Calculate averages
        for cat, stats in category_stats.items():
            n = len(stats['sites'])
            stats['average_expected'] = round(sum(stats['expected_scores']) / n, 1)
            stats['average_actual'] = round(sum(stats['actual_scores']) / n, 1)
            stats['average_difference'] = round(sum(stats['differences']) / n, 1)
            stats['average_abs_error'] = round(sum(abs(d) for d in stats['differences']) / n, 1)
        
        return category_stats
    
    def _identify_scoring_issues(self) -> Dict:
        """Identify systematic scoring issues"""
        issues = {
            'categories_consistently_low': [],
            'categories_consistently_high': [],
            'sites_with_largest_errors': [],
            'scoring_component_issues': {}
        }
        
        # Track category-level issues
        category_diffs = {}
        for result in self.results:
            for cat, diff_data in result['category_differences'].items():
                if cat not in category_diffs:
                    category_diffs[cat] = []
                category_diffs[cat].append(diff_data['difference'])
        
        # Identify consistently off categories
        for cat, diffs in category_diffs.items():
            avg_diff = sum(diffs) / len(diffs)
            if avg_diff < -5:
                issues['categories_consistently_low'].append({
                    'category': cat,
                    'average_underscoring': round(avg_diff, 1)
                })
            elif avg_diff > 5:
                issues['categories_consistently_high'].append({
                    'category': cat,
                    'average_overscoring': round(avg_diff, 1)
                })
        
        # Find worst offenders
        sorted_by_error = sorted(self.results, key=lambda x: abs(x['difference']), reverse=True)
        issues['sites_with_largest_errors'] = [
            {
                'name': r['name'],
                'expected': r['expected_score'],
                'actual': r['actual_score'],
                'difference': r['difference']
            }
            for r in sorted_by_error[:5]
        ]
        
        return issues
    
    def _generate_calibration_recommendations(self) -> Dict:
        """Generate actionable calibration recommendations"""
        recommendations = {
            'priority': [],
            'weight_adjustments': {},
            'formula_changes': []
        }
        
        # Analyze if scoring is systematically off
        summary = self._generate_summary()
        avg_diff = summary['average_difference']
        
        if abs(avg_diff) > 10:
            recommendations['priority'].append({
                'issue': f'Systematic {"under" if avg_diff < 0 else "over"}scoring by {abs(avg_diff):.1f} points on average',
                'action': 'Review all scoring formulas for excessive strictness or leniency',
                'severity': 'CRITICAL'
            })
        
        # Analyze category-specific issues
        issues = self._identify_scoring_issues()
        
        for cat_issue in issues['categories_consistently_low']:
            cat = cat_issue['category']
            diff = cat_issue['average_underscoring']
            recommendations['weight_adjustments'][cat] = {
                'current_issue': f'Underscoring by {abs(diff):.1f} points',
                'suggested_action': 'Increase max_score or make formulas more lenient',
                'priority': 'HIGH'
            }
        
        for cat_issue in issues['categories_consistently_high']:
            cat = cat_issue['category']
            diff = cat_issue['average_overscoring']
            recommendations['weight_adjustments'][cat] = {
                'current_issue': f'Overscoring by {diff:.1f} points',
                'suggested_action': 'Decrease max_score or make formulas stricter',
                'priority': 'MEDIUM'
            }
        
        return recommendations
    
    def print_summary_report(self):
        """Print human-readable summary to console"""
        if not self.results:
            print("No results to report")
            return
        
        report = self.generate_report()
        summary = report['summary']
        
        print("\n" + "="*80)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*80)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Sites Tested: {summary['total_sites_tested']}")
        print(f"  Average Expected Score: {summary['average_expected_score']}/100")
        print(f"  Average Actual Score: {summary['average_actual_score']}/100")
        print(f"  Average Error: {summary['average_difference']:+.1f} points")
        print(f"  Average Absolute Error: {summary['average_absolute_error']:.1f} points")
        print(f"  Systematic Bias: {summary['systematic_bias'].upper()}")
        
        print(f"\n🎯 Accuracy Metrics:")
        acc = summary['accuracy_metrics']
        print(f"  Within ±5 points: {acc['within_5_points']['count']}/{summary['total_sites_tested']} ({acc['within_5_points']['percentage']}%)")
        print(f"  Within ±10 points: {acc['within_10_points']['count']}/{summary['total_sites_tested']} ({acc['within_10_points']['percentage']}%)")
        print(f"  Within ±15 points: {acc['within_15_points']['count']}/{summary['total_sites_tested']} ({acc['within_15_points']['percentage']}%)")
        
        print(f"\n📂 Category Analysis:")
        for cat, stats in report['category_analysis'].items():
            print(f"\n  {cat.upper()}:")
            print(f"    Expected: {stats['average_expected']}/100")
            print(f"    Actual: {stats['average_actual']}/100")
            print(f"    Error: {stats['average_difference']:+.1f} points")
        
        print(f"\n🚨 Biggest Issues:")
        for site in report['scoring_issues']['sites_with_largest_errors']:
            print(f"  • {site['name']}: Expected {site['expected']}, Got {site['actual']} (Δ {site['difference']:+.1f})")
        
        print(f"\n💡 Calibration Recommendations:")
        for rec in report['calibration_recommendations']['priority']:
            print(f"  [{rec['severity']}] {rec['issue']}")
            print(f"    → {rec['action']}")
        
        print("\n" + "="*80 + "\n")


async def main():
    """Main execution"""
    runner = BenchmarkRunner()
    
    # Load benchmark sites
    runner.load_benchmark_sites(BENCHMARK_FILE)
    
    # Run all benchmarks
    await runner.run_all_benchmarks()
    
    # Generate and display report
    runner.print_summary_report()
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runner.generate_report(f"benchmark_report_{timestamp}.json")
    
    print(f"✅ Benchmark complete! Detailed report saved to benchmark_results/")


if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""
Baseline test runner for modified_datetime_fix BEFORE DazzleTreeLib integration.
This captures the current state of all tests and functionality.
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime

def run_command(cmd):
    """Run a command and capture output."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    return result

def run_test_baseline():
    """Run comprehensive test baseline."""
    print("=" * 80)
    print("MODIFIED_DATETIME_FIX TEST BASELINE - BEFORE DAZZLETREELIB")
    print(f"Date: {datetime.now().isoformat()}")
    print("=" * 80)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'performance': {},
        'functionality': {}
    }
    
    # 1. Run all unit tests
    print("\n1. Running all unit tests...")
    test_result = run_command("python -m pytest tests/ -v --tb=short --json-report --json-report-file=test_report.json")
    results['tests']['exit_code'] = test_result.returncode
    results['tests']['stdout'] = test_result.stdout[-5000:]  # Last 5000 chars
    
    # Parse test results
    if Path('test_report.json').exists():
        with open('test_report.json') as f:
            test_data = json.load(f)
            results['tests']['summary'] = test_data.get('summary', {})
    
    # 2. Test basic functionality
    print("\n2. Testing basic functionality...")
    test_commands = [
        # Test help
        ("Help display", "python -m folder_datetime_fix --help"),
        # Test version
        ("Version display", "python -m folder_datetime_fix --version"),
        # Test dry-run on current directory
        ("Dry run", "python -m folder_datetime_fix . --dry-run --depth 1"),
        # Test different strategies
        ("Shallow strategy", "python -m folder_datetime_fix . --dry-run --strategy shallow --depth 1"),
        ("Deep strategy", "python -m folder_datetime_fix . --dry-run --strategy deep --depth 1"),
        ("Smart strategy", "python -m folder_datetime_fix . --dry-run --strategy smart --depth 1"),
        # Test analysis modes
        ("Standard analysis", "python -m folder_datetime_fix . --dry-run --analyze standard --depth 1"),
        ("Low-memory analysis", "python -m folder_datetime_fix . --dry-run --analyze low-memory --depth 1"),
        ("Tree analysis", "python -m folder_datetime_fix . --dry-run --analyze tree --depth 1"),
        ("Folder-only analysis", "python -m folder_datetime_fix . --dry-run --analyze folder-only --depth 1"),
    ]
    
    for name, cmd in test_commands:
        print(f"  - {name}...")
        result = run_command(cmd)
        results['functionality'][name] = {
            'exit_code': result.returncode,
            'success': result.returncode == 0
        }
    
    # 3. Performance baseline
    print("\n3. Creating performance baseline...")
    
    # Create a test tree
    test_dir = Path("test_runs/baseline_tree")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create structure: 3 levels deep, 3 folders per level
    for i in range(3):
        level1 = test_dir / f"level1_{i}"
        level1.mkdir(exist_ok=True)
        (level1 / "file1.txt").write_text("test")
        
        for j in range(3):
            level2 = level1 / f"level2_{j}"
            level2.mkdir(exist_ok=True)
            (level2 / "file2.txt").write_text("test")
            
            for k in range(3):
                level3 = level2 / f"level3_{k}"
                level3.mkdir(exist_ok=True)
                (level3 / "file3.txt").write_text("test")
    
    # Benchmark different strategies
    strategies = ['shallow', 'deep', 'smart']
    for strategy in strategies:
        print(f"  - Benchmarking {strategy} strategy...")
        start = time.perf_counter()
        result = run_command(f"python -m folder_datetime_fix {test_dir} --dry-run --strategy {strategy} --depth-to 3")
        elapsed = time.perf_counter() - start
        
        results['performance'][f'{strategy}_time'] = elapsed
        results['performance'][f'{strategy}_success'] = result.returncode == 0
    
    # 4. Save baseline
    baseline_file = Path("tests/baseline_results.json")
    with open(baseline_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n4. Baseline saved to {baseline_file}")
    
    # 5. Summary
    print("\n" + "=" * 80)
    print("BASELINE SUMMARY")
    print("=" * 80)
    
    if 'summary' in results['tests']:
        summary = results['tests']['summary']
        print(f"Tests: {summary.get('total', 0)} total")
        print(f"  Passed: {summary.get('passed', 0)}")
        print(f"  Failed: {summary.get('failed', 0)}")
        print(f"  Errors: {summary.get('errors', 0)}")
    
    print("\nFunctionality tests:")
    for name, result in results['functionality'].items():
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {name}")
    
    print("\nPerformance baseline:")
    for strategy in strategies:
        if f'{strategy}_time' in results['performance']:
            print(f"  {strategy}: {results['performance'][f'{strategy}_time']:.3f}s")
    
    return results

if __name__ == "__main__":
    results = run_test_baseline()
    
    # Exit with error if any tests failed
    if results['tests']['exit_code'] != 0:
        print("\n⚠️  Some tests failed in baseline. Check test_report.json for details.")
        sys.exit(1)
    
    print("\n✅ Baseline successfully captured!")
    sys.exit(0)
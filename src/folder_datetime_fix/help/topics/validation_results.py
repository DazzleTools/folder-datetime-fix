"""
Help content validation results.

This module contains the results of validating help content claims against
the actual code implementation.
"""

from typing import Dict, List, Tuple

def get_validation_results() -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Get validation results for help content claims.
    
    Returns:
        Dict mapping topics to claims to validation results
        Format: {topic: {claim: {status, evidence, notes}}}
    """
    return {
        'strategy': {
            'SHALLOW examines only immediate children': {
                'status': '[CONFIRMED]',
                'evidence': 'folder_scanner.py:149 get_shallow_timestamp() only examines direct children',
                'notes': 'Function iterates over folder.iterdir() without recursion'
            },
            'DEEP recursively examines entire subtree': {
                'status': '[CONFIRMED]', 
                'evidence': 'folder_scanner.py:201 get_deep_timestamp() uses recursive scanning',
                'notes': 'Uses os.walk() for recursive traversal of entire tree'
            },
            'SMART automatically chooses strategy': {
                'status': '[CONFIRMED]',
                'evidence': 'folder_scanner.py:264 get_smart_timestamp() has decision logic',
                'notes': 'Checks if folder has subdirectories, uses deep if yes, shallow if no'
            }
        },
        'analyze': {
            'AUTO calculates based on 1% RAM threshold': {
                'status': '[CONFIRMED]',
                'evidence': 'analysis_strategies.py:525 target_memory = total_memory * 0.01',
                'notes': 'AutoStrategy.get_system_threshold() uses exactly 1% of system RAM'
            },
            'Memory usage ~350 bytes per folder': {
                'status': '[CONFIRMED]',
                'evidence': 'analysis_strategies.py:507 BYTES_PER_ENTRY = 350',
                'notes': 'AutoStrategy class constant defines cache entry size'
            },
            'TREE builds complete hierarchy': {
                'status': '[CONFIRMED]',
                'evidence': 'analysis_strategies.py has TreeStrategy class',
                'notes': 'TreeStrategy implementation builds in-memory tree structure'
            },
            'LOW-MEMORY < 1MB regardless of size': {
                'status': '[NEEDS_VERIFICATION]',
                'evidence': 'Implementation found but memory usage not measured',
                'notes': 'LowMemoryStrategy exists but actual memory usage not validated'
            }
        }
    }

def get_accuracy_summary() -> Dict[str, float]:
    """Get accuracy percentages by topic."""
    results = get_validation_results()
    summary = {}
    
    for topic, claims in results.items():
        total_claims = len(claims)
        confirmed_claims = sum(1 for claim in claims.values() if claim['status'].startswith('[CONFIRMED]'))
        accuracy = confirmed_claims / total_claims * 100
        summary[topic] = accuracy
    
    return summary

def print_validation_report():
    """Print a formatted validation report."""
    results = get_validation_results()
    summary = get_accuracy_summary()
    
    print("HELP CONTENT VALIDATION REPORT")
    print("=" * 50)
    print()
    
    for topic, claims in results.items():
        print(f"{topic.upper()} HELP VALIDATION:")
        print("-" * 30)
        
        for claim, validation in claims.items():
            print(f"{validation['status']} {claim}")
            print(f"   Evidence: {validation['evidence']}")
            if validation['notes']:
                print(f"   Notes: {validation['notes']}")
            print()
        
        print(f"Accuracy: {summary[topic]:.0f}%")
        print()
    
    overall_accuracy = sum(summary.values()) / len(summary)
    print(f"OVERALL ACCURACY: {overall_accuracy:.0f}%")
    print()
    
    print("LEGEND:")
    print("[CONFIRMED] - Claim verified in code")
    print("[NEEDS_VERIFICATION] - Claim exists but not fully tested")
    print("[INCORRECT] - Claim contradicted by code")

if __name__ == '__main__':
    print_validation_report()
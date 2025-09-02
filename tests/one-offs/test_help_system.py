"""
Test the new help system to show how it works.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from folder_datetime_fix.help_lib import HelpContent, HelpSection, HelpBuilder
from folder_datetime_fix.help.sections.basic import basic_section


def test_basic_functionality():
    """Test basic help system functionality."""
    
    print("=" * 60)
    print("HELP SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Create a help builder
    builder = HelpBuilder(prog='fdtfix.py')
    
    # Add the basic section
    builder.add_section(basic_section)
    
    # Show how the same content can be formatted differently
    print("1. MINIMAL HELP (no args):")
    print("-" * 40)
    minimal = builder.build_minimal_help(section_ids=['basic'], max_per_section=3)
    print(minimal)
    print()
    
    print("2. STANDARD HELP (--help):")
    print("-" * 40)
    standard = builder.build_standard_help()
    print(standard)
    print()
    
    print("3. RANDOM TIP (from non-displayed items):")
    print("-" * 40)
    tip = builder.get_random_tip()
    print(tip)
    print()
    
    # Show how to get specific items
    print("4. CUSTOM SELECTION (just dry-run examples):")
    print("-" * 40)
    dry_run_item = basic_section.get_items_by_ids(['basic.dry_run'])[0]
    print(f"As example: {dry_run_item.format_as_example('fdtfix.py')}")
    print(f"As tip: {dry_run_item.format_as_tip('fdtfix.py')}")
    print()
    
    # Show different formatting styles
    print("5. SAME CONTENT, DIFFERENT FORMATS:")
    print("-" * 40)
    recursive_item = basic_section.get_items_by_ids(['basic.recursive'])[0]
    
    print("As example:")
    print(f"  {recursive_item.format_as_example('fdtfix.py')}")
    
    print("\nAs tip:")
    print(f"  {recursive_item.format_as_tip('fdtfix.py')}")
    
    print("\nAs command only:")
    print(f"  {recursive_item.get_command('fdtfix.py')}")
    
    print("\nWith custom path:")
    print(f"  {recursive_item.get_command('fdtfix.py', path='D:\\MyFolder')}")
    print()
    
    # Show context filtering
    print("6. CONTEXT FILTERING:")
    print("-" * 40)
    minimal_items = basic_section.get_items_for_context('minimal')
    print(f"Items for 'minimal' context: {len(minimal_items)}")
    for item in minimal_items:
        print(f"  - {item.id}: {item.description}")
    
    print()
    standard_items = basic_section.get_items_for_context('standard')
    print(f"Items for 'standard' context: {len(standard_items)}")
    for item in standard_items:
        print(f"  - {item.id}: {item.description}")


def test_deduplication():
    """Test that the system tracks what's been displayed."""
    
    print()
    print("=" * 60)
    print("DEDUPLICATION TEST")
    print("=" * 60)
    print()
    
    builder = HelpBuilder(prog='fdtfix.py')
    builder.add_section(basic_section)
    
    # Build minimal help (displays some items)
    print("Building minimal help...")
    builder.build_minimal_help(max_per_section=3)
    print(f"Displayed IDs: {builder.displayed_ids}")
    print()
    
    # Get a tip (should exclude displayed items)
    print("Getting random tip (should exclude displayed items)...")
    tip = builder.get_random_tip(exclude_displayed=True)
    if tip:
        print(f"Tip: {tip}")
    else:
        print("No tips available (all items displayed)")
    
    print(f"Now displayed: {builder.displayed_ids}")


if __name__ == '__main__':
    test_basic_functionality()
    test_deduplication()
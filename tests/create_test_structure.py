"""
Create test directory structure for folder datetime fix tool testing.
Creates a 3-level deep directory structure with controlled timestamps.
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path

def set_file_times(filepath, timestamp):
    """Set both access and modified time for a file."""
    timestamp_seconds = timestamp.timestamp()
    os.utime(filepath, (timestamp_seconds, timestamp_seconds))

def create_test_structure(base_path):
    """
    Create a comprehensive test directory structure.
    
    Structure:
    test_root/
    ├── level0_empty/                    (empty folder - edge case)
    ├── level0_only_system/              (only system files)
    │   ├── thumbs.db (2024-01-01)
    │   └── desktop.ini (2024-01-01)
    ├── level0_mixed/                    (mix of system and user files)
    │   ├── thumbs.db (2024-01-01)
    │   ├── document.txt (2024-06-15)
    │   └── level1_a/
    │       ├── file_a.txt (2024-03-01)
    │       └── level2_a/
    │           └── deep_file.txt (2024-09-01)
    ├── level0_normal/                   (normal user files)
    │   ├── readme.md (2024-07-01)
    │   ├── level1_b/
    │   │   ├── data.json (2024-08-01)
    │   │   ├── .DS_Store (2024-01-01)  (system file)
    │   │   └── level2_b/
    │   │       ├── output.log (2024-09-15)
    │   │       └── level3_deep/
    │   │           └── bottom.txt (2024-10-01)
    │   └── level1_c/
    │       └── config.ini (2024-05-01)
    └── level0_recent/                   (test with very recent files)
        ├── new_file.txt (2024-12-25)
        ├── thumbs.db (2024-12-30)      (system file newer than user file!)
        └── level1_d/
            └── latest.doc (2024-12-20)
    """
    
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)
    
    # Define our test timestamps
    # Key insight: System files are typically NEWER (created when browsing)
    # This corrupts folder timestamps, which is what we're fixing
    timestamps = {
        # User file timestamps (older)
        'march': datetime(2024, 3, 1, 12, 0, 0),
        'may': datetime(2024, 5, 1, 12, 0, 0),
        'june': datetime(2024, 6, 15, 12, 0, 0),
        'july': datetime(2024, 7, 1, 12, 0, 0),
        'august': datetime(2024, 8, 1, 12, 0, 0),
        'september': datetime(2024, 9, 1, 12, 0, 0),
        'sept15': datetime(2024, 9, 15, 12, 0, 0),
        'october': datetime(2024, 10, 1, 12, 0, 0),
        
        # System file timestamps (newer - these corrupt the folder dates!)
        'system_recent': datetime(2024, 12, 25, 12, 0, 0),  # thumbs.db created recently
        'system_very_recent': datetime(2024, 12, 30, 12, 0, 0),  # desktop.ini created very recently
    }
    
    # Create level0_empty - empty folder
    empty_dir = base / 'level0_empty'
    empty_dir.mkdir(exist_ok=True)
    
    # Create level0_only_system - only system files
    sys_only = base / 'level0_only_system'
    sys_only.mkdir(exist_ok=True)
    
    thumbs = sys_only / 'thumbs.db'
    thumbs.write_text('fake thumbnail data')
    set_file_times(thumbs, timestamps['system_recent'])
    
    desktop_ini = sys_only / 'desktop.ini'
    desktop_ini.write_text('[.ShellClassInfo]')
    set_file_times(desktop_ini, timestamps['system_very_recent'])
    
    # Create level0_mixed - mixed content with depth
    mixed = base / 'level0_mixed'
    mixed.mkdir(exist_ok=True)
    
    thumbs_mixed = mixed / 'thumbs.db'
    thumbs_mixed.write_text('fake thumbnail data')
    set_file_times(thumbs_mixed, timestamps['system_very_recent'])  # System file newer than user files!
    
    doc = mixed / 'document.txt'
    doc.write_text('User document content')
    set_file_times(doc, timestamps['june'])
    
    # Level 1 under mixed
    level1_a = mixed / 'level1_a'
    level1_a.mkdir(exist_ok=True)
    
    file_a = level1_a / 'file_a.txt'
    file_a.write_text('Level 1 content')
    set_file_times(file_a, timestamps['march'])
    
    # Level 2 under mixed
    level2_a = level1_a / 'level2_a'
    level2_a.mkdir(exist_ok=True)
    
    deep_file = level2_a / 'deep_file.txt'
    deep_file.write_text('Level 2 content')
    set_file_times(deep_file, timestamps['september'])
    
    # Create level0_normal - normal files with 3 levels of depth
    normal = base / 'level0_normal'
    normal.mkdir(exist_ok=True)
    
    readme = normal / 'readme.md'
    readme.write_text('# README')
    set_file_times(readme, timestamps['july'])
    
    # Level 1_b with system file
    level1_b = normal / 'level1_b'
    level1_b.mkdir(exist_ok=True)
    
    data = level1_b / 'data.json'
    data.write_text('{"test": "data"}')
    set_file_times(data, timestamps['august'])
    
    ds_store = level1_b / '.DS_Store'
    ds_store.write_bytes(b'\x00\x00\x00\x00')  # Binary file
    set_file_times(ds_store, timestamps['system_recent'])  # System file newer than user files
    
    # Level 2_b
    level2_b = level1_b / 'level2_b'
    level2_b.mkdir(exist_ok=True)
    
    output = level2_b / 'output.log'
    output.write_text('Log file content\n')
    set_file_times(output, timestamps['sept15'])
    
    # Level 3 - deepest level
    level3_deep = level2_b / 'level3_deep'
    level3_deep.mkdir(exist_ok=True)
    
    bottom = level3_deep / 'bottom.txt'
    bottom.write_text('Deepest file')
    set_file_times(bottom, timestamps['october'])
    
    # Level 1_c 
    level1_c = normal / 'level1_c'
    level1_c.mkdir(exist_ok=True)
    
    config = level1_c / 'config.ini'
    config.write_text('[Settings]\nkey=value')
    set_file_times(config, timestamps['may'])
    
    # Create level0_recent - demonstrate the core problem
    # User file from October, but thumbs.db created in December when browsing
    recent = base / 'level0_recent'
    recent.mkdir(exist_ok=True)
    
    user_file = recent / 'project_notes.txt'
    user_file.write_text('Last edited in October')
    set_file_times(user_file, timestamps['october'])  # User last touched in October
    
    thumbs_recent = recent / 'thumbs.db'
    thumbs_recent.write_text('fake thumbnail data')
    set_file_times(thumbs_recent, timestamps['system_very_recent'])  # Created when browsing in December!
    
    level1_d = recent / 'level1_d'
    level1_d.mkdir(exist_ok=True)
    
    doc = level1_d / 'report.doc'
    doc.write_text('September report')
    set_file_times(doc, timestamps['september'])  # Older document
    
    print(f"Test structure created at: {base}")
    print("\nExpected behaviors:")
    print("1. level0_empty: Should keep current timestamp (no files)")
    print("2. level0_only_system: Without -sg: gets system file time (Dec); With -sg: no change")
    print("3. level0_mixed: Without -sg: corrupted to Dec; With -sg: gets June (shallow) or Sept (deep)")
    print("4. level0_normal: Should get Oct (deep) or July (shallow)")
    print("5. level0_recent: Without -sg: corrupted to Dec 30; With -sg: gets Oct (actual user file)")
    
    return base

def create_test_expectations():
    """
    Return expected timestamps for different processing strategies.
    
    Key scenarios:
    - System files (thumbs.db, desktop.ini) are NEWER than user files
    - Without --skip-generated, folders get corrupted to December dates
    - With --skip-generated, folders show actual user file dates
    """
    return {
        'shallow_no_skip': {
            'level0_empty': None,  # No change
            'level0_only_system': datetime(2024, 12, 30, 12, 0, 0),  # Gets system file time
            'level0_mixed': datetime(2024, 12, 30, 12, 0, 0),  # Corrupted by thumbs.db!
            'level0_normal': datetime(2024, 7, 1, 12, 0, 0),  # No system files at root
            'level0_recent': datetime(2024, 12, 30, 12, 0, 0),  # Corrupted by thumbs.db
        },
        'shallow_skip_generated': {
            'level0_empty': None,  # No change
            'level0_only_system': None,  # No user files to use
            'level0_mixed': datetime(2024, 6, 15, 12, 0, 0),  # Gets actual user file
            'level0_normal': datetime(2024, 7, 1, 12, 0, 0),  # readme.md
            'level0_recent': datetime(2024, 10, 1, 12, 0, 0),  # Gets actual user file (October)
        },
        'deep_no_skip': {
            'level0_empty': None,
            'level0_only_system': datetime(2024, 12, 30, 12, 0, 0),  # System files
            'level0_mixed': datetime(2024, 12, 30, 12, 0, 0),  # Corrupted by thumbs.db
            'level0_normal': datetime(2024, 12, 25, 12, 0, 0),  # Corrupted by .DS_Store in subfolder
            'level0_recent': datetime(2024, 12, 30, 12, 0, 0),  # Corrupted by thumbs.db
        },
        'deep_skip_generated': {
            'level0_empty': None,
            'level0_only_system': None,  # No user files
            'level0_mixed': datetime(2024, 9, 1, 12, 0, 0),  # deep_file.txt in level2
            'level0_normal': datetime(2024, 10, 1, 12, 0, 0),  # bottom.txt in level3
            'level0_recent': datetime(2024, 10, 1, 12, 0, 0),  # project_notes.txt
        }
    }

if __name__ == '__main__':
    test_path = Path(__file__).parent / 'test_structure'
    create_test_structure(test_path)
    
    print("\n" + "="*50)
    print("Test expectations:")
    expectations = create_test_expectations()
    for strategy, results in expectations.items():
        print(f"\n{strategy}:")
        for folder, timestamp in results.items():
            if timestamp:
                print(f"  {folder}: {timestamp.strftime('%Y-%m-%d')}")
            else:
                print(f"  {folder}: No change")
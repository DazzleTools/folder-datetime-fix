"""
System-generated files that should be excluded with --skip-generated flag.
"""

# System-generated files that are typically not user-created
SYSTEM_GENERATED_FILES = {
    # Windows thumbnail caches
    'thumbs.db',
    'Thumbs.db',  # Sometimes capitalized
    'ehthumbs.db',
    'ehthumbs_vista.db',
    
    # Windows folder settings
    'desktop.ini',
    'Desktop.ini',
    'folder.htt',
    'folder.gif',
    
    # Windows system files
    'IconCache.db',
    'hiberfil.sys',
    'pagefile.sys',
    'swapfile.sys',
    
    # macOS system files
    '.DS_Store',
    '.localized',
    '.Spotlight-V100',
    '.fseventsd',
    '.TemporaryItems',
    '.Trashes',
    '.VolumeIcon.icns',
    '.com.apple.timemachine.donotpresent',
    
    # macOS resource forks
    '._*',  # Pattern: AppleDouble format files
    
    # Linux/Unix desktop environments
    '.directory',  # KDE folder settings
    '.hidden',     # GNOME hidden file list
    
    # Cloud sync markers
    '.dropbox',
    '.dropbox.cache',
    '.dropbox.attr',
    'desktop.ini',  # OneDrive uses this too
    '.sync',
    '.owncloudsync.log',
    
    # Version control indexes (debatable - might want separate flag)
    '.git/index',
    '.git/index.lock',
    '.svn/entries',
    '.hg/dirstate',
    
    # IDE/Editor files (debatable - might want separate flag)
    '.vscode/settings.json',
    '.idea/',
    '.vs/',
    '*.swp',  # Vim swap files
    '*~',     # Emacs/general backup files
    
    # Package manager caches
    'node_modules/.cache/',
    '__pycache__/',
    '.pytest_cache/',
    
    # Temporary files
    '~$*',  # MS Office temp files
    '.tmp',
    '*.tmp',
}

def is_system_generated(filename):
    """
    Check if a filename matches system-generated patterns.
    
    Args:
        filename: Name of the file (not full path)
    
    Returns:
        bool: True if file appears to be system-generated
    """
    filename_lower = filename.lower()
    
    # Check exact matches
    if filename_lower in {f.lower() for f in SYSTEM_GENERATED_FILES if not f.startswith('*') and not f.endswith('*')}:
        return True
    
    # Check patterns
    # AppleDouble files
    if filename.startswith('._'):
        return True
    
    # MS Office temp files
    if filename.startswith('~$'):
        return True
    
    # General temp/backup files
    if filename.startswith('~') or filename.endswith('~'):
        return True
    
    # .tmp files
    if filename.endswith('.tmp') or filename.endswith('.swp'):
        return True
    
    return False
"""
System-generated files and folders that should be excluded with --skip-generated flag.
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
    '.sync',
    '.owncloudsync.log',
    
    # Version control index files
    '.git/index',
    '.git/index.lock',
    '.svn/entries',
    '.hg/dirstate',
    
    # IDE/Editor specific files
    '.vscode/settings.json',
    '*.swp',  # Vim swap files
    '*~',     # Emacs/general backup files
    
    # Temporary files
    '~$*',  # MS Office temp files
    '.tmp',
    '*.tmp',
}

# System-generated folders that should be excluded
SYSTEM_GENERATED_FOLDERS = {
    # Python
    '__pycache__',
    '.pytest_cache',
    
    # Version control
    '.git',
    '.svn',
    '.hg',
    '.bzr',
    
    # IDEs and editors
    '.idea',
    '.vscode',
    '.vs',
    '.venv',
    'venv',
    '.virtualenv',
    
    # Node.js
    'node_modules',
    '.npm',
    '.yarn',
    
    # macOS
    '.Spotlight-V100',
    '.fseventsd',
    '.TemporaryItems',
    '.Trashes',
    
    # Build outputs
    'build',
    'dist',
    'target',
    '.gradle',
    '.maven',
    
    # Cache directories
    '.cache',
    '.sass-cache',
    '.parcel-cache',
}

def is_system_generated(filename):
    """
    Check if a filename or folder name matches system-generated patterns.
    
    Args:
        filename: Name of the file or directory (not full path)
    
    Returns:
        bool: True if file/folder appears to be system-generated
    """
    filename_lower = filename.lower()
    
    # Check if it's a system-generated folder
    if filename_lower in {f.lower() for f in SYSTEM_GENERATED_FOLDERS}:
        return True
    
    # Check exact file matches
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
# Scripts Directory

Utility scripts for development, diagnostics, and operations of the folder-datetime-fix project.

## Directory Structure

```
scripts/
├── setup/                 # Environment setup and validation
│   ├── setup_dev_environment.bat
│   ├── validate_dev_environment.py
│   └── README.md
├── unctools/             # UNCtools-specific diagnostics
│   ├── diagnose_unctools_env.py
│   ├── debug_module_import.py
│   └── README.md
└── README.md             # This file
```

## Quick Start

### Setting Up Development Environment
```cmd
# Run automated setup
scripts\setup\setup_dev_environment.bat

# Or validate existing environment
python scripts/setup/validate_dev_environment.py
```

### Troubleshooting Import Issues
```bash
# For UNCtools-specific issues
python scripts/unctools/diagnose_unctools_env.py

# For general module import debugging
python scripts/unctools/debug_module_import.py
```

## Subdirectories

### `setup/` - Environment Setup & Validation
Tools for setting up and validating development environments:
- Automated Windows setup script
- Python environment validator
- Dependency installation helpers

See `setup/README.md` for detailed usage.

### `unctools/` - UNCtools Diagnostics
Specialized diagnostic tools for UNCtools integration:
- Environment diagnostic for import issues
- Module-level import state analysis
- Cross-environment testing utilities

See `unctools/README.md` for detailed usage and troubleshooting workflows.

## Adding New Scripts

When adding scripts to this directory:

1. **Choose appropriate subdirectory**:
   - `setup/` - Environment configuration, installation, validation
   - `unctools/` - UNCtools-specific tools
   - Create new subdirectory for other categories

2. **Follow naming conventions**:
   - Use descriptive names (e.g., `validate_dev_environment.py`)
   - Prefix with action verb (validate, diagnose, setup, etc.)
   - Use `.py` for Python scripts, `.bat`/`.sh` for shell scripts

3. **Include documentation**:
   - Add docstring/comments in the script
   - Update relevant README files
   - Include usage examples

4. **Test across environments**:
   - Standard Windows CMD
   - PowerShell
   - Git Bash
   - Special shells (e.g., dazzle shell)

## Script Categories

### Development Tools
- Environment setup and validation
- Dependency management
- Development workflow automation

### Diagnostic Tools
- Import troubleshooting
- Environment analysis
- Performance profiling

### Operational Scripts
- Build automation
- Deployment helpers
- Maintenance utilities

## Future Additions

Potential script categories to add:
- `build/` - Build and packaging scripts
- `test/` - Test runners and helpers
- `deploy/` - Deployment automation
- `maintenance/` - Cleanup and maintenance tools

## Related Documentation

- Main project README: `../README.md`
- Test documentation: `../tests/README.md`
- Private documentation: `../private/claude/`

## Contributing

See subdirectory README files for specific guidelines on each script category.
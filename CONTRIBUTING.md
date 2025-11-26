# Contributing to CC-Packer

Thank you for your interest in contributing to CC-Packer! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected behavior vs actual behavior
- Your system information (Windows version, Fallout 4 installation path type, etc.)
- Any error messages or logs

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- A clear description of the feature
- Why this feature would be useful
- How you envision it working

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test your changes thoroughly
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Open a Pull Request

#### Pull Request Guidelines

- Follow the existing code style
- Add comments for complex logic
- Update documentation if needed
- Test with multiple Fallout 4 installations if possible
- Keep PRs focused on a single feature or bug fix

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Fallout 4 with Creation Club content
- Creation Kit (for Archive2.exe)

### Installation

```bash
# Clone the repository
git clone https://github.com/jturnley/CC-Packer.git
cd CC-Packer

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Building

```bash
# Build standalone executable
build_exe.bat

# Build release packages
build_release.bat
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

Before submitting a PR:
- Test on a clean Fallout 4 installation
- Test with various numbers of CC content (few, many, all)
- Test the restore functionality
- Test error handling (missing files, no permissions, etc.)

## Questions?

Feel free to open an issue for any questions about contributing!

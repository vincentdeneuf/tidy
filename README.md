# Tidy

A CLI tool named tidy for cleaning Python code.

## Installation

```bash
pip install tidy
```

## Usage

```bash
tidy <command> [options]
```

### Commands

- `tidy comments` - Remove comments from Python files
- `tidy prints` - Remove print statements from Python files  
- `tidy docstrings` - Remove docstrings from Python files
- `tidy asserts` - Remove assert statements from Python files
- `tidy logs` - Remove logging statements from Python files

### Examples

```bash
# Remove all print statements
tidy prints

# Remove inline comments only (preserve noqa, type:, pragma)
tidy comments --default

# Remove all types of comments
tidy comments --all

# Remove specific log levels
tidy logs --debug --info --error

# Remove all log levels
tidy logs --all

# Show per-file details (verbose is default)
tidy prints

# Suppress per-file output
tidy prints --quiet
```

## Development

This project uses a src-layout packaging structure.

### Requirements

- Python >= 3.11
- LibCST

## License

MIT License

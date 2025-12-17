# Unabbreviator

A command-line tool for expanding custom abbreviations in text and markdown documents. Designed for processing notes taken during meetings or interviews where personal shorthand is used.

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
# Process a file (overwrites original)
python unabbreviator.py document.txt

# Process a file and write to a different output file
python unabbreviator.py notes.txt notes_expanded.txt

# Preview changes without saving
python unabbreviator.py --dry-run document.txt

# Use a custom abbreviations file
python unabbreviator.py -a ~/my-abbreviations.yml document.txt

# Process the frontmost document in a macOS app (TextEdit, Typora, etc.)
python unabbreviator.py --gui
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `FILE` | Input file to process |
| `OUTPUT` | Optional output file (if omitted, overwrites input) |
| `--gui` | Process frontmost document in a macOS application |
| `-a, --abbreviations PATH` | Path to abbreviations YAML file |
| `-n, --dry-run` | Show changes without modifying files |
| `--help` | Show help message |

## How It Works

The tool scans each word in your document and:

1. **Known abbreviation** (in `abbreviations.yml`): Prompts you to choose an expansion
2. **Unknown word not in system dictionary**: Prompts you to provide an expansion or skip
3. **Regular dictionary word**: Skips silently

### Interactive Options

When prompted for a word, you have these options:

| Key | Action |
|-----|--------|
| `1-9` | Select a numbered expansion |
| `n` | Add a new expansion (saves to abbreviations.yml) |
| `e` | Provide expansion for unknown word (saves to abbreviations.yml) |
| `s` | Skip (keep word as-is) |
| `i` | Ignore (never prompt for this word again, saves to ignored.yml) |
| `o` | Once (expand with custom text, don't save to abbreviations) |
| `v` | Save current changes and stop processing |
| `a` | Abort (discard all changes, revert to original) |

### Progress Bar

Each prompt displays a progress bar showing how far through the document you are:

```
[██████████░░░░░░░░░░░░░░░░░░░░] 8/23 words (34%)
```

## Configuration Files

### abbreviations.yml

Stores your abbreviation mappings. Each entry has an abbreviation (`brev`) and one or more expansions (`terms`):

```yaml
- brev: govt
  terms:
    - government
- brev: econ
  terms:
    - economy
    - economic
    - economics
```

When an abbreviation has multiple expansions, you'll be prompted to choose which one to use.

### ignored.yml

Stores words you've chosen to permanently ignore. These words will never trigger a prompt:

```yaml
- we've
- shouldn't
- misc
```

Both files are stored in the same directory as `unabbreviator.py` by default, or alongside a custom abbreviations file if specified with `-a`.

## macOS GUI Mode

With `--gui`, the tool attempts to get the file path of the frontmost document from supported applications:

- TextEdit
- Typora
- Other document-based apps (via generic AppleScript)

This allows integration with your preferred text editor without needing to specify the file path manually.

## License

MIT

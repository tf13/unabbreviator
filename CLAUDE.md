# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unabbreviator is an abbreviation expansion tool. The `abbreviations.yml` file contains mappings from abbreviated terms (`brev`) to their possible full forms (`terms`).

The purpose of the app is to expand custom abbreviations in documents of notes taken during meetings and/or interviews. The app should be primarily or entirely written in python. 

Users will run the app on a plain text or markdown document, either from the command line or within existing writing apps such as Typora, MultimarkdownComposer 5, Marked, TextEdit, etc. (any document-based text- or markdown editing app should work) — i.e., the app itself needs to operate on a file (CLI) or frontmost open document (GUI), rather than having a document opening/editing GUI of its own. The interface should be intuitive, unobtrusive and well-documented. 

Where the user is asked for input on a given word, the word should be shown in context (e.g., the full line in which the word appears, and for shorter lines also the preceding and succeeding lines). 

These abbreviations are highly idiosyncratic, so the app must check against the `abbreviations.yml` file, which contains entries for abbreviations and expansions. No other source should be considered for matching words to expansions. Any given abbreviation could have more than one potential expansion, and some abbreviations may match ordinary words (e.g., "man" could be an abbreviation for "manual" but could also just be the word "man"). The app must not add abbreviations or terms to the YAML file without user approval.

For any word in the document, if the word has an entry in `abbreviations.yml`, the user should be prompted and given a choice of either expanding the abbreviation (if there is only one expansion available), choosing an expansion (if more than one expansion is available), providing a new expansion for the abbreviation (which will then be added to the YAML file) or skipping. If no abbreviation is found for a given word **and** the word is in the system dictionary, no user interaction is required — the app should skip this word. If, however, there is no entry in the YAML file and the word is NOT in the system dictionary, then the user should be prompted and given a choice of skipping the word (i.e., leaving it as-is in the document) or providing an expansion (which the app will then add with the word to the YAML file). 

The YAML file in the directory includes some entries already, demonstrating the syntax that should be used. 


## Usage

```bash
# Process a file
python unabbreviator.py document.txt

# Process frontmost document in a macOS app (TextEdit, Typora, etc.)
python unabbreviator.py --gui

# Preview changes without saving
python unabbreviator.py --dry-run document.txt

# Use a custom abbreviations file
python unabbreviator.py -a ~/my-abbreviations.yml document.txt
```

## Development Environment

- Always use the `.venv` virtual environment; if one doesn't exist, create it with `python3 -m venv .venv`
- Activate with `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Code Style

- Follow PEP 8
- Use click for CLI interfaces
- Use [ApexMarkdown/apex](https://github.com/ApexMarkdown/apex) for Markdown processing if needed

## Data Format

The `abbreviations.yml` file structure:
```yaml
- brev: <abbreviation>
  terms:
    - <possible expansion 1>
    - <possible expansion 2>
```

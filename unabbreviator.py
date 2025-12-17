#!/usr/bin/env python3
"""
Unabbreviator - Expand custom abbreviations in text documents.

This tool processes plain text or markdown documents, prompting the user
to expand abbreviations defined in abbreviations.yml.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import click
import yaml


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.resolve()


def load_abbreviations(yaml_path):
    """Load abbreviations from YAML file."""
    if not yaml_path.exists():
        return {}

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    # Convert list format to dict for easier lookup
    abbrevs = {}
    for entry in data:
        brev = entry.get('brev', '').lower()
        terms = entry.get('terms', [])
        if brev and terms:
            abbrevs[brev] = terms
    return abbrevs


def save_abbreviations(yaml_path, abbreviations):
    """Save abbreviations back to YAML file."""
    # Convert dict back to list format
    data = []
    for brev in sorted(abbreviations.keys()):
        data.append({
            'brev': brev,
            'terms': abbreviations[brev]
        })

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_ignored_words(ignored_path):
    """Load ignored words from YAML file."""
    if not ignored_path.exists():
        return set()

    with open(ignored_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []

    return set(word.lower() for word in data)


def save_ignored_words(ignored_path, ignored_words):
    """Save ignored words to YAML file."""
    data = sorted(ignored_words)

    with open(ignored_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_system_dictionary():
    """Load system dictionary words into a set."""
    dict_paths = [
        '/usr/share/dict/words',  # macOS and most Linux
        '/usr/dict/words',
    ]

    words = set()
    for dict_path in dict_paths:
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    words.add(line.strip().lower())
            break

    return words


def get_word_variants(word):
    """Generate possible base forms of a word by stripping common suffixes."""
    word = word.lower()
    variants = [word]

    # Common irregular forms mapping to base words
    irregulars = {
        'has': 'have', 'had': 'have', 'having': 'have',
        'is': 'be', 'am': 'be', 'are': 'be', 'was': 'be', 'were': 'be', 'been': 'be', 'being': 'be',
        'does': 'do', 'did': 'do', 'done': 'do', 'doing': 'do',
        'goes': 'go', 'went': 'go', 'gone': 'go', 'going': 'go',
        'says': 'say', 'said': 'say', 'saying': 'say',
        'makes': 'make', 'made': 'make', 'making': 'make',
        'takes': 'take', 'took': 'take', 'taken': 'take', 'taking': 'take',
        'comes': 'come', 'came': 'come', 'coming': 'come',
        'sees': 'see', 'saw': 'see', 'seen': 'see', 'seeing': 'see',
        'knows': 'know', 'knew': 'know', 'known': 'know', 'knowing': 'know',
        'gets': 'get', 'got': 'get', 'gotten': 'get', 'getting': 'get',
        'gives': 'give', 'gave': 'give', 'given': 'give', 'giving': 'give',
        'finds': 'find', 'found': 'find', 'finding': 'find',
        'thinks': 'think', 'thought': 'think', 'thinking': 'think',
        'tells': 'tell', 'told': 'tell', 'telling': 'tell',
        'becomes': 'become', 'became': 'become', 'becoming': 'become',
        'leaves': 'leave', 'left': 'leave', 'leaving': 'leave',
        'feels': 'feel', 'felt': 'feel', 'feeling': 'feel',
        'puts': 'put', 'putting': 'put',
        'brings': 'bring', 'brought': 'bring', 'bringing': 'bring',
        'begins': 'begin', 'began': 'begin', 'begun': 'begin', 'beginning': 'begin',
        'keeps': 'keep', 'kept': 'keep', 'keeping': 'keep',
        'holds': 'hold', 'held': 'hold', 'holding': 'hold',
        'writes': 'write', 'wrote': 'write', 'written': 'write', 'writing': 'write',
        'stands': 'stand', 'stood': 'stand', 'standing': 'stand',
        'hears': 'hear', 'heard': 'hear', 'hearing': 'hear',
        'lets': 'let', 'letting': 'let',
        'means': 'mean', 'meant': 'mean', 'meaning': 'mean',
        'sets': 'set', 'setting': 'set',
        'meets': 'meet', 'met': 'meet', 'meeting': 'meet',
        'runs': 'run', 'ran': 'run', 'running': 'run',
        'pays': 'pay', 'paid': 'pay', 'paying': 'pay',
        'sits': 'sit', 'sat': 'sit', 'sitting': 'sit',
        'speaks': 'speak', 'spoke': 'speak', 'spoken': 'speak', 'speaking': 'speak',
        'lies': 'lie', 'lay': 'lie', 'lain': 'lie', 'lying': 'lie',
        'leads': 'lead', 'led': 'lead', 'leading': 'lead',
        'reads': 'read', 'reading': 'read',
        'grows': 'grow', 'grew': 'grow', 'grown': 'grow', 'growing': 'grow',
        'loses': 'lose', 'lost': 'lose', 'losing': 'lose',
        'falls': 'fall', 'fell': 'fall', 'fallen': 'fall', 'falling': 'fall',
        'sends': 'send', 'sent': 'send', 'sending': 'send',
        'builds': 'build', 'built': 'build', 'building': 'build',
        'understands': 'understand', 'understood': 'understand', 'understanding': 'understand',
        'draws': 'draw', 'drew': 'draw', 'drawn': 'draw', 'drawing': 'draw',
        'breaks': 'break', 'broke': 'break', 'broken': 'break', 'breaking': 'break',
        'spends': 'spend', 'spent': 'spend', 'spending': 'spend',
        'cuts': 'cut', 'cutting': 'cut',
        'catches': 'catch', 'caught': 'catch', 'catching': 'catch',
        'chooses': 'choose', 'chose': 'choose', 'chosen': 'choose', 'choosing': 'choose',
        'wears': 'wear', 'wore': 'wear', 'worn': 'wear', 'wearing': 'wear',
        'eats': 'eat', 'ate': 'eat', 'eaten': 'eat', 'eating': 'eat',
        'drives': 'drive', 'drove': 'drive', 'driven': 'drive', 'driving': 'drive',
        'rises': 'rise', 'rose': 'rise', 'risen': 'rise', 'rising': 'rise',
        'wins': 'win', 'won': 'win', 'winning': 'win',
        'throws': 'throw', 'threw': 'throw', 'thrown': 'throw', 'throwing': 'throw',
        'flies': 'fly', 'flew': 'fly', 'flown': 'fly', 'flying': 'fly',
        'hits': 'hit', 'hitting': 'hit',
        'buys': 'buy', 'bought': 'buy', 'buying': 'buy',
        'teaches': 'teach', 'taught': 'teach', 'teaching': 'teach',
        'sells': 'sell', 'sold': 'sell', 'selling': 'sell',
        'fights': 'fight', 'fought': 'fight', 'fighting': 'fight',
        'sleeps': 'sleep', 'slept': 'sleep', 'sleeping': 'sleep',
        'costs': 'cost', 'costing': 'cost',
        'shuts': 'shut', 'shutting': 'shut',
        'forgets': 'forget', 'forgot': 'forget', 'forgotten': 'forget', 'forgetting': 'forget',
    }

    if word in irregulars:
        variants.append(irregulars[word])

    # Common suffix patterns and their replacements
    suffix_rules = [
        # Plurals and verb forms
        ('ies', 'y'),      # policies -> policy
        ('ies', 'ie'),     # cookies -> cookie
        ('es', ''),        # changes -> chang, boxes -> box
        ('es', 'e'),       # changes -> change
        ('s', ''),         # notes -> note
        # Past tense and -ing
        ('ied', 'y'),      # tried -> try
        ('ed', ''),        # changed -> chang
        ('ed', 'e'),       # changed -> change
        ('ing', ''),       # working -> work
        ('ing', 'e'),      # making -> make
        # Doubling consonant
        ('ning', 'n'),     # running -> run
        ('ting', 't'),     # hitting -> hit
        ('ping', 'p'),     # stopping -> stop
        ('bing', 'b'),     # grabbing -> grab
        ('ding', 'd'),     # adding -> add
        ('ging', 'g'),     # hugging -> hug
        ('ming', 'm'),     # swimming -> swim
        # -er, -est
        ('ier', 'y'),      # happier -> happy
        ('iest', 'y'),     # happiest -> happy
        ('er', ''),        # worker -> work
        ('er', 'e'),       # larger -> large
        ('est', ''),       # largest -> larg
        ('est', 'e'),      # largest -> large
        # -ly
        ('ly', ''),        # quickly -> quick
        ('ily', 'y'),      # happily -> happy
        # -tion, -ness, etc.
        ('tion', 't'),     # creation -> creat (partial)
        ('ness', ''),      # happiness -> happi (partial)
        ('ment', ''),      # government -> govern
        ('able', ''),      # workable -> work
        ('able', 'e'),     # lovable -> love
        ('ible', ''),      # possible -> poss (partial)
    ]

    for suffix, replacement in suffix_rules:
        if word.endswith(suffix):
            base = word[:-len(suffix)] + replacement
            if len(base) >= 2:  # Don't create too-short words
                variants.append(base)

    return variants


def is_in_dictionary(word, dictionary):
    """Check if a word or any of its base forms is in the system dictionary."""
    variants = get_word_variants(word)
    return any(v in dictionary for v in variants)


def extract_words(text):
    """Extract words and their positions from text."""
    # Match words (including contractions and hyphenated words)
    pattern = r"\b[a-zA-Z]+(?:[''-][a-zA-Z]+)*\b"

    words = []
    for match in re.finditer(pattern, text):
        words.append({
            'word': match.group(),
            'start': match.start(),
            'end': match.end()
        })
    return words


def get_context(text, start, end, context_lines=1):
    """Get the context around a word position."""
    lines = text.split('\n')

    # Find which line contains the word
    char_count = 0
    target_line_idx = 0
    for i, line in enumerate(lines):
        line_end = char_count + len(line)
        if char_count <= start <= line_end:
            target_line_idx = i
            break
        char_count = line_end + 1  # +1 for newline

    # Get surrounding lines
    start_idx = max(0, target_line_idx - context_lines)
    end_idx = min(len(lines), target_line_idx + context_lines + 1)

    context_text = '\n'.join(lines[start_idx:end_idx])
    return context_text, target_line_idx - start_idx


def apply_case(original, replacement):
    """Apply the case pattern of original to replacement."""
    if original.isupper():
        return replacement.upper()
    elif original.istitle():
        return replacement.capitalize()
    else:
        return replacement.lower()


def format_progress_bar(current, total, width=30):
    """Format a text-based progress bar."""
    if total == 0:
        percent = 100
    else:
        percent = int((current / total) * 100)

    filled = int(width * current / total) if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {current}/{total} words ({percent}%)"


def prompt_for_expansion(word, context, terms, is_known_abbrev, current_word=0, total_words=0):
    """
    Prompt user to choose an expansion for a word.

    Returns a dict with:
        - action: 'skip', 'expand', 'ignore', 'once', 'save', 'abort'
        - expansion: the expansion text (if applicable)
        - add_to_yaml: whether to add to YAML
    """
    click.echo()
    click.echo(click.style('─' * 60, fg='blue'))

    # Show progress bar
    if total_words > 0:
        progress = format_progress_bar(current_word, total_words)
        click.echo(click.style(progress, fg='magenta'))

    click.echo(click.style('Context:', fg='cyan', bold=True))

    # Highlight the word in context
    highlighted = context.replace(word, click.style(word, fg='yellow', bold=True))
    click.echo(f"  {highlighted}")
    click.echo()

    if is_known_abbrev:
        click.echo(click.style(f'Found abbreviation: ', fg='cyan') +
                   click.style(word, fg='yellow', bold=True))

        # Expansion options - highlighted in green
        click.echo(click.style('Expansions:', fg='green', bold=True))
        for i, term in enumerate(terms, 1):
            click.echo(click.style(f"  [{i}] {term}", fg='green', bold=True))
        click.echo(click.style(f"  [n] New expansion...", fg='green'))

        # Action options - dimmer
        click.echo(click.style('Actions:', dim=True))
        click.echo(click.style("  [s] Skip    [i] Ignore    [o] Once...", dim=True))
        click.echo(click.style("  [v] Save & stop    [a] Abort", dim=True))

        while True:
            choice = click.prompt('Choose', default='s').strip().lower()

            if choice == 's':
                return {'action': 'skip', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'i':
                return {'action': 'ignore', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'v':
                return {'action': 'save', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'a':
                return {'action': 'abort', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'o':
                new_term = click.prompt('Enter expansion (one-time)').strip()
                if new_term:
                    return {'action': 'once', 'expansion': new_term, 'add_to_yaml': False}
                click.echo(click.style('Empty expansion not allowed.', fg='red'))
            elif choice == 'n':
                new_term = click.prompt('Enter new expansion').strip()
                if new_term:
                    return {'action': 'expand', 'expansion': new_term, 'add_to_yaml': True}
                click.echo(click.style('Empty expansion not allowed.', fg='red'))
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(terms):
                    return {'action': 'expand', 'expansion': terms[idx], 'add_to_yaml': False}
                click.echo(click.style('Invalid choice.', fg='red'))
            else:
                click.echo(click.style('Invalid choice.', fg='red'))
    else:
        click.echo(click.style(f'Unknown word: ', fg='cyan') +
                   click.style(word, fg='yellow', bold=True))

        # Expansion options - highlighted in green
        click.echo(click.style('Expansions:', fg='green', bold=True))
        click.echo(click.style(f"  [e] Add expansion...", fg='green', bold=True))

        # Action options - dimmer
        click.echo(click.style('Actions:', dim=True))
        click.echo(click.style("  [s] Skip    [i] Ignore    [o] Once...", dim=True))
        click.echo(click.style("  [v] Save & stop    [a] Abort", dim=True))

        while True:
            choice = click.prompt('Choose', default='s').strip().lower()

            if choice == 's':
                return {'action': 'skip', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'i':
                return {'action': 'ignore', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'v':
                return {'action': 'save', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'a':
                return {'action': 'abort', 'expansion': None, 'add_to_yaml': False}
            elif choice == 'o':
                new_term = click.prompt('Enter expansion (one-time)').strip()
                if new_term:
                    return {'action': 'once', 'expansion': new_term, 'add_to_yaml': False}
                click.echo(click.style('Empty expansion not allowed.', fg='red'))
            elif choice == 'e':
                new_term = click.prompt('Enter expansion').strip()
                if new_term:
                    return {'action': 'expand', 'expansion': new_term, 'add_to_yaml': True}
                click.echo(click.style('Empty expansion not allowed.', fg='red'))
            else:
                click.echo(click.style('Invalid choice.', fg='red'))


def process_document(text, abbreviations, dictionary, yaml_path, ignored_words, ignored_path):
    """
    Process a document, prompting for abbreviation expansions.

    Returns:
        - text: the processed text
        - modified: whether any changes were made
        - aborted: whether user chose to abort (discard changes)
    """
    words = extract_words(text)
    total_words = len(words)
    replacements = []  # List of (start, end, replacement)
    modified = False

    # Track words we've already prompted about (to avoid asking twice for same word)
    prompted_words = set()

    for word_index, word_info in enumerate(words):
        word = word_info['word']
        word_lower = word.lower()

        # Skip if we've already prompted about this word form or it's ignored
        if word_lower in prompted_words or word_lower in ignored_words:
            continue

        is_known_abbrev = word_lower in abbreviations
        in_dict = is_in_dictionary(word, dictionary)

        if is_known_abbrev:
            # Known abbreviation - prompt user
            terms = abbreviations[word_lower]
            context, _ = get_context(text, word_info['start'], word_info['end'])

            result = prompt_for_expansion(word, context, terms, True, word_index + 1, total_words)
            action = result['action']

            if action == 'abort':
                click.echo(click.style('Aborted. No changes saved.', fg='red'))
                return text, False, True

            if action == 'save':
                click.echo(click.style('Saving and stopping...', fg='yellow'))
                # Apply current replacements and return
                if replacements:
                    replacements.sort(key=lambda x: x[0], reverse=True)
                    for start, end, replacement in replacements:
                        text = text[:start] + replacement + text[end:]
                return text, modified, False

            if action == 'ignore':
                ignored_words.add(word_lower)
                save_ignored_words(ignored_path, ignored_words)
                click.echo(click.style(f'Added "{word_lower}" to ignored words.', fg='green'))
                prompted_words.add(word_lower)
                continue

            if action in ('expand', 'once') and result['expansion']:
                expansion = result['expansion']
                # Find all occurrences of this word and queue for replacement
                for w in words:
                    if w['word'].lower() == word_lower:
                        replacements.append((w['start'], w['end'], apply_case(w['word'], expansion)))

                # Add new term to abbreviations only if not 'once'
                if result['add_to_yaml'] and expansion not in abbreviations[word_lower]:
                    abbreviations[word_lower].append(expansion)
                    save_abbreviations(yaml_path, abbreviations)
                    click.echo(click.style(f'Added "{expansion}" to abbreviations for "{word_lower}".', fg='green'))

                modified = True

            prompted_words.add(word_lower)

        elif not in_dict:
            # Unknown word not in dictionary - prompt user
            context, _ = get_context(text, word_info['start'], word_info['end'])

            result = prompt_for_expansion(word, context, [], False, word_index + 1, total_words)
            action = result['action']

            if action == 'abort':
                click.echo(click.style('Aborted. No changes saved.', fg='red'))
                return text, False, True

            if action == 'save':
                click.echo(click.style('Saving and stopping...', fg='yellow'))
                # Apply current replacements and return
                if replacements:
                    replacements.sort(key=lambda x: x[0], reverse=True)
                    for start, end, replacement in replacements:
                        text = text[:start] + replacement + text[end:]
                return text, modified, False

            if action == 'ignore':
                ignored_words.add(word_lower)
                save_ignored_words(ignored_path, ignored_words)
                click.echo(click.style(f'Added "{word_lower}" to ignored words.', fg='green'))
                prompted_words.add(word_lower)
                continue

            if action in ('expand', 'once') and result['expansion']:
                expansion = result['expansion']
                # Find all occurrences of this word and queue for replacement
                for w in words:
                    if w['word'].lower() == word_lower:
                        replacements.append((w['start'], w['end'], apply_case(w['word'], expansion)))

                # Add new abbreviation only if not 'once'
                if result['add_to_yaml']:
                    abbreviations[word_lower] = [expansion]
                    save_abbreviations(yaml_path, abbreviations)
                    click.echo(click.style(f'Added abbreviation "{word_lower}" -> "{expansion}".', fg='green'))

                modified = True

            prompted_words.add(word_lower)

    # Apply replacements in reverse order to preserve positions
    if replacements:
        # Sort by position descending
        replacements.sort(key=lambda x: x[0], reverse=True)
        for start, end, replacement in replacements:
            text = text[:start] + replacement + text[end:]

    return text, modified, False


def get_frontmost_document_macos():
    """Get the path of the frontmost document on macOS using AppleScript."""
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
    end tell

    if frontApp is "TextEdit" then
        tell application "TextEdit"
            if (count of documents) > 0 then
                set docPath to path of document 1
                return docPath
            end if
        end tell
    else if frontApp is "Typora" then
        tell application "Typora"
            if (count of documents) > 0 then
                return path of document 1
            end if
        end tell
    else
        -- Try generic approach for document-based apps
        tell application frontApp
            try
                if (count of documents) > 0 then
                    return path of document 1
                end if
            end try
        end tell
    end if
    return ""
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        path = result.stdout.strip()
        if path and os.path.exists(path):
            return path
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


@click.command()
@click.argument('file', type=click.Path(exists=True), required=False)
@click.argument('output', type=click.Path(), required=False)
@click.option('--gui', is_flag=True, help='Use frontmost document (macOS only)')
@click.option('--abbreviations', '-a', type=click.Path(),
              help='Path to abbreviations YAML file (default: abbreviations.yml in script directory)')
@click.option('--dry-run', '-n', is_flag=True, help='Show changes without modifying the file')
def main(file, output, gui, abbreviations, dry_run):
    """
    Expand abbreviations in a text or markdown document.

    If FILE is provided, process that file. Optionally specify OUTPUT to write
    to a different file (preserving the original). With --gui, process the
    frontmost document in a supported macOS application.

    Examples:

        unabbreviator notes.txt

        unabbreviator notes.txt notes_expanded.txt

        unabbreviator --gui

        unabbreviator -a ~/my-abbreviations.yml document.md
    """
    # Determine file to process
    if gui:
        if sys.platform != 'darwin':
            raise click.ClickException('--gui option is only available on macOS')

        file_path = get_frontmost_document_macos()
        if not file_path:
            raise click.ClickException(
                'Could not get frontmost document. Make sure a document is open '
                'in a supported application (TextEdit, Typora, etc.)'
            )
        file_path = Path(file_path)
    elif file:
        file_path = Path(file)
    else:
        raise click.ClickException('Please provide a FILE or use --gui')

    # Determine abbreviations file path
    if abbreviations:
        yaml_path = Path(abbreviations)
    else:
        yaml_path = get_script_dir() / 'abbreviations.yml'

    if not yaml_path.exists():
        raise click.ClickException(f'Abbreviations file not found: {yaml_path}')

    # Ignored words file is alongside abbreviations file
    ignored_path = yaml_path.parent / 'ignored.yml'

    click.echo(click.style(f'Processing: {file_path}', fg='cyan'))
    click.echo(click.style(f'Using abbreviations: {yaml_path}', fg='cyan'))
    click.echo()

    # Load data
    abbrevs = load_abbreviations(yaml_path)
    ignored_words = load_ignored_words(ignored_path)
    dictionary = load_system_dictionary()

    click.echo(f'Loaded {len(abbrevs)} abbreviations, {len(ignored_words)} ignored words, {len(dictionary)} dictionary words')

    # Read document
    with open(file_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # Process document
    processed_text, modified, aborted = process_document(
        original_text, abbrevs, dictionary, yaml_path, ignored_words, ignored_path
    )

    if aborted:
        # User chose to abort - don't save anything
        return

    if not modified:
        click.echo()
        click.echo(click.style('No changes made.', fg='yellow'))
        return

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = file_path

    # Write or display results
    if dry_run:
        click.echo()
        click.echo(click.style('─' * 60, fg='blue'))
        click.echo(click.style('Dry run - changes not saved:', fg='yellow', bold=True))
        click.echo(processed_text)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        click.echo()
        click.echo(click.style(f'File saved: {output_path}', fg='green', bold=True))


if __name__ == '__main__':
    main()

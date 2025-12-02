"""Demo harness for file_organizer

Creates a temporary folder, populates sample files and shows dry-run output.
Run as a local smoke-test.
"""

import tempfile
from pathlib import Path
import shutil

from file_organizer import organize


def make_sample_dir(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    samples = {
        'photo1.JPG': b'1',
        'photo2.png': b'2',
        'document1.pdf': b'3',
        'spreadsheet1.csv': b'4',
        'music1.MP3': b'5',
        'archive1.zip': b'6',
        'script.py': b'print(42)',
        'notes.txt': b'hello',
    }

    for name, content in samples.items():
        (base / name).write_bytes(content)


def demo():
    tmp = Path(tempfile.mkdtemp(prefix='file-organizer-demo-'))
    try:
        print('Demo folder:', tmp)
        make_sample_dir(tmp)

        # Dry run
        print('\n==== Dry-run ===')
        results, summary = organize(tmp, recursive=False, dry_run=True)
        print('Summary:', summary)

        # Now perform actual move
        print('\n==== Real run ===')
        results2, summary2 = organize(tmp, recursive=False, dry_run=False)
        print('Summary:', summary2)

        print('\nFinal tree:')
        for p in sorted(tmp.rglob('*')):
            print(' ', p.relative_to(tmp))

    finally:
        # Clean up the temp demo folder
        shutil.rmtree(tmp)


if __name__ == '__main__':
    demo()

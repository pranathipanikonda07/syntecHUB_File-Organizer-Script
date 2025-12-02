"""File Organizer

Scans a directory and moves files into subfolders based on file extensions.

Features:
- Extension -> folder mapping (default mapping built-in)
- Recursive scanning option
- Dry-run mode (no file system changes)
- Logging of moved files to a CSV file and stdout summaries
- Safe collision handling (appends counter suffix to avoid overwrites)

Usage examples:
    python file_organizer.py --path "C:\Users\You\Desktop" --dry-run
    python file_organizer.py -p "C:\Users\You\Downloads" -r

This file is intended to be cross-platform but scheduling examples in
the README focus on Windows Task Scheduler (optional).
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_MAP: Dict[str, str] = {
    # images
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images', '.bmp': 'Images', '.svg': 'Images',
    # documents
    '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents', '.odt': 'Documents', '.txt': 'Documents', '.rtf': 'Documents',
    # spreadsheets
    '.xls': 'Spreadsheets', '.xlsx': 'Spreadsheets', '.csv': 'Spreadsheets',
    # presentations
    '.ppt': 'Presentations', '.pptx': 'Presentations',
    # archives
    '.zip': 'Archives', '.tar': 'Archives', '.gz': 'Archives', '.rar': 'Archives', '.7z': 'Archives',
    # media
    '.mp4': 'Video', '.mkv': 'Video', '.mov': 'Video', '.avi': 'Video',
    '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio',
    # code
    '.py': 'Code', '.js': 'Code', '.ts': 'Code', '.java': 'Code', '.c': 'Code', '.cpp': 'Code', '.cs': 'Code', '.html': 'Code', '.css': 'Code',
}


@dataclass
class MoveResult:
    src: Path
    dest: Path
    moved: bool
    reason: Optional[str] = None


def find_files(path: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for p in path.rglob('*'):
            if p.is_file():
                yield p
    else:
        for p in path.iterdir():
            if p.is_file():
                yield p


def ext_to_folder(extension: str, mapping: Dict[str, str]) -> str:
    return mapping.get(extension.lower(), 'Others')


def unique_destination(dest: Path) -> Path:
    """If dest exists, append a numeric suffix before extension until unique.

    Examples:
        file.txt -> file (1).txt -> file (2).txt
    """
    if not dest.exists():
        return dest

    parent = dest.parent
    stem = dest.stem
    suffix = dest.suffix

    idx = 1
    while True:
        candidate = parent / f"{stem} ({idx}){suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def move_file(src: Path, dest: Path, dry_run: bool) -> MoveResult:
    dest_dir = dest.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    if src.resolve() == dest.resolve():
        return MoveResult(src=src, dest=dest, moved=False, reason='same_path')

    final_dest = unique_destination(dest)

    if dry_run:
        return MoveResult(src=src, dest=final_dest, moved=False, reason='dry_run')

    try:
        shutil.move(str(src), str(final_dest))
        return MoveResult(src=src, dest=final_dest, moved=True)
    except Exception as exc:  # broad exception just to report errors to the caller
        return MoveResult(src=src, dest=final_dest, moved=False, reason=str(exc))


def organize(
    folder: Path,
    mapping: Optional[Dict[str, str]] = None,
    recursive: bool = False,
    dry_run: bool = False,
) -> Tuple[List[MoveResult], Dict[str, int]]:
) -> Tuple[List[MoveResult], Dict[str, int]]:
    mapping = mapping or DEFAULT_MAP
    results: List[MoveResult] = []

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    files = list(find_files(folder, recursive=recursive))

    summary: Dict[str, int] = {'examined': 0, 'moved': 0, 'skipped': 0, 'errors': 0}

    for file in files:
        summary['examined'] += 1

        extension = file.suffix.lower()
        folder_name = ext_to_folder(extension, mapping)

        target_dir = folder / folder_name
        dest_path = target_dir / file.name

        # Skip moving if file is already in the destination folder path
        try:
            # Use parts comparison so we can detect nested location by name too
            if file.parent.resolve() == target_dir.resolve():
                results.append(MoveResult(src=file, dest=dest_path, moved=False, reason='already_in_target'))
                summary['skipped'] += 1
                continue
        except Exception:
            # ignore resolution errors
            pass

        res = move_file(file, dest_path, dry_run=dry_run)
        results.append(res)
        if res.moved:
            summary['moved'] += 1
        else:
            if res.reason == 'dry_run' or res.reason == 'already_in_target' or res.reason == 'same_path':
                summary['skipped'] += 1
            else:
                summary['errors'] += 1

    return results, summary

    return results, summary


def write_log_csv(csv_path: Path, results: List[MoveResult]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    header = ['timestamp', 'src', 'dest', 'moved', 'reason']

    with csv_path.open('a', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        # Add header if file is empty
        if csv_path.stat().st_size == 0:
            writer.writerow(header)

        ts = datetime.utcnow().isoformat() + 'Z'
        for r in results:
            writer.writerow([ts, str(r.src), str(r.dest), str(r.moved), r.reason or ''])


def write_human_log(log_path: Path, results: List[MoveResult]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open('a', encoding='utf-8') as fh:
        ts = datetime.utcnow().isoformat() + 'Z'
        for r in results:
            line = f"{ts}\t{r.src}\t->\t{r.dest}\tmoved={r.moved}\t{r.reason or ''}\n"
            fh.write(line)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Organize files in a folder into subfolders by extension')
    p.add_argument('-p', '--path', required=True, help='Folder to scan and organize')
    p.add_argument('-r', '--recursive', action='store_true', help='Scan folders recursively')
    p.add_argument('--dry-run', action='store_true', help='Do not move files, only show what would happen')
    p.add_argument('--log', help='Path to CSV log file where moves are appended (default: ./organizer_log.csv)')
    p.add_argument('--log-human', help='Path to a human readable log file for moved files (optional)')
    p.add_argument('--map', help='Optional mapping CSV (ext,folder) to override/extend defaults')
    return p.parse_args()


def load_mapping_from_csv(path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with path.open('r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                ext, folder = parts[0], parts[1]
                if not ext.startswith('.'):
                    ext = '.' + ext
                mapping[ext.lower()] = folder

    return mapping


def main() -> None:
    args = parse_args()

    folder = Path(args.path).expanduser()
    mapping = dict(DEFAULT_MAP)
    if args.map:
        mapping.update(load_mapping_from_csv(Path(args.map)))

    log_path = Path(args.log) if args.log else Path.cwd() / 'organizer_log.csv'
    human_log_path = Path(args.log_human) if getattr(args, 'log_human', None) else None

    # Setup console logger for warnings/errors
    logger = logging.getLogger('file_organizer')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logger.addHandler(handler)

    print(f"Scanning: {folder}")
    print(f"Recursive: {args.recursive}, Dry-run: {args.dry_run}")
    print(f"Log file: {log_path}")

    results, summary = organize(folder, mapping=mapping, recursive=args.recursive, dry_run=args.dry_run)

    # Write logs
    if log_path:
        write_log_csv(log_path, results)
    if human_log_path:
        write_human_log(human_log_path, results)

    # Add console logging for moved items and warnings
    for r in results:
        if r.moved:
            logger.info(f"Moved: {r.src} -> {r.dest}")
        else:
            if r.reason in ('dry_run', 'already_in_target', 'same_path'):
                logger.debug(f"Skipped: {r.src} -> reason={r.reason}")
            else:
                logger.warning(f"Failed to move {r.src} -> {r.dest} (reason={r.reason})")

    print('\nSummary:')
    print(f"  Examined: {summary['examined']}")
    print(f"  Moved:    {summary['moved']}")
    print(f"  Skipped:  {summary['skipped']}")
    print(f"  Errors:   {summary['errors']}")

    if args.dry_run:
        print('\nDry run — no files were actually moved. To apply changes run without --dry-run')


if __name__ == '__main__':
    main()

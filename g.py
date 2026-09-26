#!/usr/bin/env python3
import argparse
import ast
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log(msg, level='INFO'):
    print(f'[{ts()}] [{level}] {msg}')


def read(path):
    return path.read_text(encoding='utf-8')


def write_py(path, content, dry_run):
    try:
        ast.parse(content)
    except SyntaxError as e:
        log(f'syntax error in {path}: {e}', 'ERROR')
        return False
    if dry_run:
        log(f'[dry-run] would write {path}')
        return True
    path.write_text(content, encoding='utf-8')
    log(f'wrote {path}')
    return True


def replace_exact(path, old, new, dry_run):
    if not path.exists():
        log(f'missing file: {path}', 'ERROR')
        return False
    content = read(path)
    if new and new in content and old not in content:
        log(f'already applied in {path}')
        return True
    count = content.count(old)
    if count == 0:
        log(f'anchor not found in {path}', 'WARN')
        return False
    if count > 1:
        log(f'anchor appears {count} times in {path}, replacing first', 'WARN')
    new_content = content.replace(old, new, 1)
    return write_py(path, new_content, dry_run)


def run(cmd, dry_run):
    if dry_run:
        log(f'[dry-run] would run: {" ".join(cmd)}')
        return True
    log(f'running: {" ".join(cmd)}')
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.stdout:
            print(r.stdout)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        if r.returncode != 0:
            log(f'command failed ({r.returncode})', 'ERROR')
            return False
        return True
    except Exception as e:
        log(f'command error: {e}', 'ERROR')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--target-dir', default='.')
    args = parser.parse_args()
    root = Path(args.target_dir).resolve()
    log(f'target: {root}')

    view_path = root / 'axis_saas' / 'views' / 'assign_teachers.py'

    # =================================================================
    # ASSIGN_PERIODS_COUNT_MERGE_FIX_V1
    #
    # The "Assigned Periods" column on the assign-teachers page showed
    # an inflated "X/Y" — e.g. 41/49 when only 41 (out of a real 41)
    # were filled. Root cause: `total_periods` summed `periods_count`
    # from EVERY timetable assigned to the class, so overlapping
    # periods on the same day were counted twice (once per timetable).
    #
    # The API grid, however, MERGES the assigned timetables into one
    # union view — days are keyed by day_of_week and periods are keyed
    # by order, so a slot shared by two timetables appears exactly
    # once. The table header contradicted the grid it opened.
    #
    # Fix: compute `total_periods` from the same merged union the API
    # uses, so both numbers agree.
    # =================================================================
    old_count = """        class_rows = []
        for g in _grouped.values():
            total_periods = 0
            for _tt in g['timetables']:
                for _d in (_tt.days or []):
                    try:
                        total_periods += int(_d.get('periods_count') or 0)
                    except (TypeError, ValueError):
                        pass
            _label_display = ', '.join(g['labels']) or 'Timetable'
            class_rows.append({"""
    new_count = """        class_rows = []
        for g in _grouped.values():
            # ASSIGN_PERIODS_COUNT_MERGE_FIX_V1: sum DISTINCT
            # (day_of_week, period_order) pairs across every timetable
            # assigned to this class. The grid the Manage button opens
            # uses the same union view (see api_get_teacher_assignments
            # — _merged_days_by_dow), so this count now matches it.
            _merged_orders = {}
            for _tt in g['timetables']:
                if _tt is None:
                    continue
                for _d in (_tt.days or []):
                    _dow = _d.get('day_of_week')
                    if _dow is None:
                        continue
                    _bucket = _merged_orders.setdefault(_dow, set())
                    for _p in (_d.get('periods') or []):
                        if _p.get('is_break'):
                            continue
                        _order = _p.get('order')
                        if _order is not None:
                            _bucket.add(_order)
            total_periods = sum(len(_s) for _s in _merged_orders.values())
            _label_display = ', '.join(g['labels']) or 'Timetable'
            class_rows.append({"""
    replace_exact(view_path, old_count, new_count, args.dry_run)

    if view_path.exists() and not args.dry_run:
        run([sys.executable, '-m', 'py_compile', str(view_path)], args.dry_run)

    log('done')


if __name__ == '__main__':
    main()

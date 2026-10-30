#!/usr/bin/env python3
"""Run only explicitly selected tests that require no proprietary firmware.

This is not the historical complete 53-test or 25-test suite. Skips fail this run.
"""
import argparse
import importlib
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'installazione_v4'))
PUBLIC_CLASSES = (
    ('test_audit_statico', 'BackupTests'),
    ('test_laboratorio', 'GuardTests'),
    ('test_fullscreen_coordinato', 'PlanTests'),
    ('test_installazione', 'ParserTests'),
    ('test_installazione', 'RootPathTests'),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-report', type=Path)
    args = parser.parse_args()
    suite = unittest.TestSuite()
    groups = []
    for module_name, class_name in PUBLIC_CLASSES:
        module = importlib.import_module(module_name)
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, class_name))
        groups.append({'module': module_name, 'class': class_name, 'tests': tests.countTestCases()})
        suite.addTests(tests)
    print('Public synthetic-input suite. No original firmware, live NAC or vehicle test.', flush=True)
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    success = result.wasSuccessful() and not result.skipped and result.testsRun > 0
    record = {'scope': 'public synthetic-input suite only', 'success': success,
              'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped),
              'elapsed_seconds': round(time.monotonic()-started, 3),
              'python': sys.version.split()[0], 'groups': groups,
              'firmware_dependent_tests_run': False, 'hardware_tests_run': False,
              'cryptographic_acceptance_proved': False}
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(record, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())

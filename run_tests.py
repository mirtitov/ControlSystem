#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов
"""

import os
import subprocess
import sys


def run_test_file(test_file):
    """Запустить тестовый файл"""
    print(f"\n{'=' * 60}")
    print(f"Running: {test_file}")
    print("=" * 60)

    result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def main():
    """Запустить все тесты"""
    test_dir = os.path.join(os.path.dirname(__file__), "tests")

    test_files = [
        os.path.join(test_dir, "test_imports.py"),
        os.path.join(test_dir, "test_schemas.py"),
        os.path.join(test_dir, "test_models.py"),
        os.path.join(test_dir, "test_api_structure.py"),
    ]

    print("\n" + "=" * 60)
    print("🧪 Starting Test Suite")
    print("=" * 60)

    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_test_file(test_file)
            results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((test_file, False))

    # Итоги
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {os.path.basename(test_file)}")

    print("=" * 60)
    print(f"Total: {passed}/{total} test suites passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

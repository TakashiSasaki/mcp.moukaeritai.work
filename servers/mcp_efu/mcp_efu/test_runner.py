import sys
import unittest
from pathlib import Path


def main() -> None:
    package_root = Path(__file__).resolve().parent
    tests_root = package_root.parent / "tests"
    suite = unittest.defaultTestLoader.discover(str(tests_root))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()

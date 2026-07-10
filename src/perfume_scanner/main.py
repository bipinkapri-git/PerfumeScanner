"""Main entry point for Perfume Scanner."""

import sys


def scan_perfume() -> str:
    """Run a placeholder perfume scan."""
    return "Perfume Scanner is active and ready to scan."


def main() -> None:
    """Run the command line entry point."""
    print("Welcome to Perfume Scanner!")
    status = scan_perfume()
    print(status)


if __name__ == "__main__":
    main()

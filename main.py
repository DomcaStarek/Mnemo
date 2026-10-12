"""Entry point for the Mnemo desktop application."""

import argparse
from pathlib import Path

from mnemo.ui.app import MnemoApp


def main() -> None:
    """Launch the Mnemo desktop application."""
    parser = argparse.ArgumentParser(
        description="Mnemo — Local Manager for Notes, Shell Commands, and Code Snippets."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Path to custom JSON data file (defaults to mnemo_data.json in app directory)",
    )
    args = parser.parse_args()

    data_path = Path(args.file).resolve() if args.file else None

    app = MnemoApp(data_file=data_path)
    app.mainloop()


if __name__ == "__main__":
    main()

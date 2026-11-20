"""Deliver the bundled news illustration to the runner's output folder.

This entrypoint has a single job: take the ``entry.png`` artwork that
sits next to this file in the repository and place a copy of it where
the evaluation harness expects to find generated output.

The destination directory is controlled through the
``MAKEFUN_OUTPUT_DIR`` environment variable and falls back to
``/output`` when the variable is not set.  The copied file always
keeps the name ``entry.png``.
"""

import os
import shutil
from pathlib import Path

OUTPUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
FALLBACK_OUTPUT_DIR = "/output"
ARTWORK_FILENAME = "entry.png"


def artwork_source() -> Path:
    """Return the path of the artwork shipped alongside this module."""
    return Path(__file__).resolve().parent / ARTWORK_FILENAME


def destination_for(folder: Path) -> Path:
    """Build the full destination path inside an output folder."""
    return folder / ARTWORK_FILENAME


def publish_artwork() -> Path:
    """Copy the bundled artwork into the configured output folder.

    Returns:
        The path of the copy that was written.

    Raises:
        FileNotFoundError: If the bundled artwork is absent from the
            repository checkout.
        OSError: If the copy operation itself fails.
    """
    origin = artwork_source()

    # The artwork is a committed asset, not something produced at
    # runtime, so a missing file means the checkout is incomplete.
    if not origin.is_file():
        raise FileNotFoundError(
            f"Required artwork is missing: {origin}. "
            "Restore it by running draw.py during the build step and "
            "committing the generated entry.png alongside main.py."
        )

    raw_target_dir = os.environ.get(OUTPUT_ENV_VAR, FALLBACK_OUTPUT_DIR)
    target_dir = Path(raw_target_dir)
    target_file = destination_for(target_dir)

    # Create the destination when needed; an existing output folder
    # is left exactly as it is and is never removed by this program.
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copyfile(origin, target_file)
    except OSError as problem:
        raise OSError(
            f"Could not copy artwork from {origin} to {target_file}: "
            f"{problem}"
        ) from problem

    return target_file


def main() -> None:
    # Entry point used when this file is executed as a script.
    written = publish_artwork()
    print(f"Delivered artwork to {written}")


if __name__ == "__main__":
    main()

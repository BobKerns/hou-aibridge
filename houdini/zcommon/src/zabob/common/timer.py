'''
Timer context manager for measuring execution time
'''

import time
import sys
from contextlib import contextmanager
from collections.abc import Callable, Generator
from typing import Any


@contextmanager
def timer(label: str) -> Generator[Callable[..., None], Any, None]:
    """
    Context manager that reports elapsed time during execution with support for subtask updates.

    Args:
        label (str): A descriptive label to identify this timer in the output

    Yields:
        Callable: An update function that can be called to report intermediate timing results
                 update(tag: str, exception: Optional[Exception] = None)

    Example:
        with timer("Processing data") as update:
            # Process first batch
            update("batch 1")

            try:
                # Process second batch
                process_batch2()
            except ValueError as e:
                update("batch 2", exception=e)
                # Handle exception

            # Process third batch
            update("batch 3")

        # Output will show timing for each batch and overall total
    """
    start_time = time.time()
    previous_time = start_time
    previous_tag = None
    has_updates = False

    def update(tag: str, exception: Exception|None = None) -> None:
        """Report timing for a subtask and start timing a new one.

        Args:
            tag: Label for the new subtask
            exception: Optional exception if the previous subtask failed
        """
        nonlocal previous_time, previous_tag, has_updates

        current_time = time.time()
        elapsed = current_time - previous_time

        if previous_tag is not None:
            if exception is None:
                print(f"{label} - {previous_tag}: completed in {elapsed:.4f} seconds", file=sys.stderr)
            else:
                print(f"{label} - {previous_tag}: failed after {elapsed:.4f} seconds - {type(exception).__name__}: {exception}",
                      file=sys.stderr)

        previous_tag = tag
        previous_time = current_time
        has_updates = True

    try:
        print(f"{label}: started", file=sys.stderr)
        yield update

        # Handle final subtask if there was one
        if has_updates and previous_tag is not None:
            end_time = time.time()
            subtask_elapsed = end_time - previous_time
            print(f"{label} - {previous_tag}: completed in {subtask_elapsed:.4f} seconds", file=sys.stderr)

        # Report total time
        end_time = time.time()
        total_elapsed = end_time - start_time
        if has_updates:
            print(f"{label}: total completed in {total_elapsed:.4f} seconds", file=sys.stderr)
        else:
            print(f"{label}: completed in {total_elapsed:.4f} seconds", file=sys.stderr)

    except Exception as e:
        end_time = time.time()

        # Handle final subtask if there was one
        if has_updates and previous_tag is not None:
            subtask_elapsed = end_time - previous_time
            print(f"{label} - {previous_tag}: failed after {subtask_elapsed:.4f} seconds - {type(e).__name__}: {e}",
                  file=sys.stderr)

        # Report total time with failure
        total_elapsed = end_time - start_time
        if has_updates:
            print(f"{label}: total failed after {total_elapsed:.4f} seconds - {type(e).__name__}: {e}",
                  file=sys.stderr)
        else:
            print(f"{label}: failed after {total_elapsed:.4f} seconds - {type(e).__name__}: {e}",
                  file=sys.stderr)
        raise

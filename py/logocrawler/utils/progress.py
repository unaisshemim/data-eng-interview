

import sys
import time


def print_progress(processed, total, found, skipped, failed, start_time, workers):

    elapsed = time.time() - start_time
    rate = processed / elapsed if elapsed > 0 else 0.0
    pct = (processed / total * 100) if total else 0.0

    bar_width = 28
    filled = int(bar_width * processed / total) if total else 0
    bar = "#" * filled + "-" * (bar_width - filled)

    msg = (
        f"\r[{bar}] {processed}/{total} ({pct:5.1f}%) "
        f"found={found} skipped={skipped} failed={failed} "
        f"rate={rate:.2f}/s workers={workers}"
    )
    sys.stderr.write(msg)
    sys.stderr.flush()

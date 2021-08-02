from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Tuple

from plover.oslayer.config import CONFIG_DIR


def get_stats(
    logs: Optional[Iterable[Path]] = None,
    update: Optional[Callable[[int], Any]] = None,
) -> Tuple:
    if logs is None:
        # There may be many log files, e.g. strokes.log, strokes.log.1, strokes.log.2 etc.
        logs = Path(CONFIG_DIR).glob("strokes.log*")

    stats_by_day = defaultdict(lambda: {"strokes": 0, "translations": 0})
    total_stroke_count = 0
    total_translation_count = 0

    progress = 0
    for log in logs:
        for line in log.read_text().splitlines():
            # yeah I'm assuming the date will always take up this much space
            timestamp, action = line[:23], line[24:]

            date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S,%f")
            key = datetime.strftime(date, "%Y-%m-%d")

            if action.startswith("Translation"):
                stats_by_day[key]["translations"] += 1
                total_translation_count += 1
            if action.startswith("Stroke"):
                stats_by_day[key]["strokes"] += 1
                total_stroke_count += 1

            if update is not None:
                progress += 1
                if progress % 10000 == 0:
                    # emitting an update on every line makes it really slow
                    update(progress)

    unique_days = len(stats_by_day.keys())

    overview_stats = (total_stroke_count, total_translation_count, unique_days)
    return overview_stats, stats_by_day

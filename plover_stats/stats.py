from collections import defaultdict
from datetime import datetime
from pathlib import Path
import pickle
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from plover.oslayer.config import CONFIG_DIR

CACHE_PATH = Path(CONFIG_DIR, "plover-stats.cache")
CACHE_VERSION = 1


def default_stats():
    return {"strokes": 0, "translations": 0}


def get_stats(
    paths: Optional[Iterable[Path]] = None,
    update: Optional[Callable[[int], Any]] = None,
) -> Tuple:
    if paths is None:
        # There may be many log files, e.g. strokes.log, strokes.log.1, strokes.log.2 etc.
        paths = Path(CONFIG_DIR).glob("strokes.log*")

    stats, paths_to_do = load_cache(paths)

    progress = 0
    for path in paths_to_do:
        path_stats = {
            "path": path,
            "stats_by_day": defaultdict(default_stats),
            "strokes": 0,
            "translations": 0,
        }

        for line in path.read_text().splitlines():
            # yeah I'm assuming the date will always take up this much space
            timestamp, action = line[:23], line[24:]

            date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S,%f")
            key = datetime.strftime(date, "%Y-%m-%d")

            if action.startswith("Translation"):
                path_stats["stats_by_day"][key]["translations"] += 1
                path_stats["translations"] += 1
            if action.startswith("Stroke"):
                path_stats["stats_by_day"][key]["strokes"] += 1
                path_stats["strokes"] += 1

            if update is not None:
                if progress % 10000 == 0:
                    # emitting an update on every line makes it really slow
                    update(progress)

                progress += 1

        stats[path] = path_stats

    stats_by_day = defaultdict(default_stats)
    strokes = 0
    translations = 0
    for path, item in stats.items():
        for day, value in item["stats_by_day"].items():
            stats_by_day[day]["strokes"] += value["strokes"]
            stats_by_day[day]["translations"] += value["translations"]
        strokes += item["strokes"]
        translations += item["translations"]
    unique_days = len(stats_by_day.keys())

    save_cache(stats)

    overview_stats = (strokes, translations, unique_days)
    return overview_stats, stats_by_day


def load_cache(paths: Iterable[Path]) -> Tuple[Dict, List]:
    stats = {}

    if not CACHE_PATH.exists():
        return stats, paths

    cache = pickle.loads(CACHE_PATH.read_bytes())

    if cache["version"] < CACHE_VERSION:
        return stats, paths

    paths_to_do = []
    for path in paths:
        if path in cache["stats"]:
            path_cache = cache["stats"][path]
            if Path(path).stat().st_mtime_ns <= path_cache["last_modified"]:
                stats[path] = path_cache
            else:
                paths_to_do.append(path)
        else:
            print("not in cache, adding to todo")
            paths_to_do.append(path)

    return stats, paths_to_do


def save_cache(new_stats: Dict) -> None:
    stats = {}
    if CACHE_PATH.exists():
        cache = pickle.loads(CACHE_PATH.read_bytes())

        if cache["version"] == CACHE_VERSION:
            stats = cache["stats"]

    for path, value in new_stats.items():
        stats[path] = value
        stats[path]["last_modified"] = Path(path).stat().st_mtime_ns

    new_cache = {"version": CACHE_VERSION, "stats": stats}

    with CACHE_PATH.open("wb") as f:
        pickle.dump(new_cache, f)

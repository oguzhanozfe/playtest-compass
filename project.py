"""Summarize observed playtest tasks without treating assisted wins as independent."""
from collections import defaultdict
from statistics import median
import math

TITLE = "Playtest Compass"
DESCRIPTION = "Compare independent wins, assisted completions, abandonments and active task time from observed playtests."
PROMPT = ("Compare task results using raw counts and observed denominators. Distinguish assisted and "
          "independent completion. Note missing timing data and avoid causal or retention claims.")


def analyze(data: dict) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("observations"), list):
        raise ValueError("Provide an observations array.")
    grouped = defaultdict(list)
    seen, players = set(), set()
    for record in data["observations"]:
        if not isinstance(record, dict):
            raise ValueError("Each observation must be an object.")
        player, task, outcome = [record.get(k) for k in ("player", "task", "outcome")]
        if any(not isinstance(s, str) or not s.strip() for s in (player, task)):
            raise ValueError("Each observation requires nonempty player and task identifiers.")
        player, task = player.strip(), task.strip()
        if outcome not in ("independent", "assisted", "abandoned"):
            raise ValueError("Use an independent, assisted or abandoned outcome.")
        duration = record.get("active_seconds")
        if duration is not None and (type(duration) not in (float, int) or duration < 0
                                     or duration > 604800 or not math.isfinite(duration)):
            raise ValueError("Use a finite active_seconds value from zero to seven days, or null.")
        if (player, task) in seen:
            raise ValueError(f"Duplicate observation for {player} and {task}.")
        seen.add((player, task))
        players.add(player)
        grouped[task].append((outcome, duration))
    rows = []
    independent = abandoned = 0
    for task, results in grouped.items():
        wins = sum(outcome == "independent" for outcome, _ in results)
        assisted = sum(outcome == "assisted" for outcome, _ in results)
        stops = len(results) - wins - assisted
        independent += wins
        abandoned += stops
        times = [s for outcome, s in results if outcome != "abandoned" and s is not None]
        stop_times = [s for outcome, s in results if outcome == "abandoned" and s is not None]
        rows.append({"Task": task, "Observed": len(results), "Independent": wins, "Assisted": assisted,
                     "Abandoned": stops, "Independent (%)": round(100 * wins / len(results), 2),
                     "Timed completions": len(times), "Median completion (s)": median(times) if times else None,
                     "Timed abandonments": len(stop_times), "Median before abandoning (s)": median(stop_times) if stop_times else None})
    return {"summary": f"{len(players)} players supplied {len(seen)} task observations. "
                       f"{independent} finished independently and {abandoned} ended in abandonment.",
            "metrics": {"Players": len(players), "Task observations": len(seen), "Independent completions": independent,
                        "Abandonments": abandoned}, "rows": rows}

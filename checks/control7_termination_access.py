"""
Control 7 checker: terminated users' access must be removed within 24 hours.

What this script does, in plain words:
  1. Reads three small data files (like exports from HR, Okta, AWS, and GitHub).
  2. For every terminated employee, looks up when each of their accounts was removed.
  3. Applies one rule: removal must happen within THRESHOLD_HOURS of the HR termination.
  4. Prints a summary and saves the results to the "results" folder.

It uses only Python's built-in tools, so nothing extra needs to be installed.
"""

import csv
import sys 
from datetime import datetime
from pathlib import Path

# ---- The rule. Change this number to see what happens. ----
THRESHOLD_HOURS = 24

# ---- Where things live. ----
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_FOLDER / "data"
RESULTS_FOLDER = PROJECT_FOLDER / "results"
TIME_FORMAT = "%Y-%m-%d %H:%M"


def read_csv(filename):
    """Open a CSV file and return its rows as a list of dictionaries."""
    with open(DATA_FOLDER / filename, newline="") as f:
        return list(csv.DictReader(f))


def parse_time(text):
    """Turn text like '2026-03-14 09:30' into a date-and-time value we can do math on."""
    return datetime.strptime(text, TIME_FORMAT)


def check_everyone():
    terminations = read_csv("hr_terminations.csv")
    entitlements = read_csv("entitlements.csv")
    removals = read_csv("removals.csv")

    # Lookup 1: which systems did each person have an account in?
    systems_by_person = {}
    for row in entitlements:
        systems_by_person.setdefault(row["emp_id"], []).append(row["system"])

    # Lookup 2: when was each (person, system) account removed?
    removed_at = {}
    for row in removals:
        removed_at[(row["emp_id"], row["system"])] = parse_time(row["removed_time"])

    results = []
    for person in terminations:
        emp_id = person["emp_id"]
        terminated = parse_time(person["termination_time"])

        problems = []      # a list of plain-English reasons this person failed
        slowest_hours = 0  # how long the slowest removal took

        for system in systems_by_person.get(emp_id, []):
            removed = removed_at.get((emp_id, system))

            if removed is None:
                # No removal record at all: the account may still be active.
                problems.append(f"{system}: no removal record, access may still be active")
                continue

            hours = (removed - terminated).total_seconds() / 3600
            slowest_hours = max(slowest_hours, hours)
            if hours > THRESHOLD_HOURS:
                problems.append(f"{system}: removed after {hours:.1f} hours")

        results.append({
            "emp_id": emp_id,
            "name": person["name"],
            "department": person["department"],
            "terminated": person["termination_time"],
            "slowest_removal_hours": round(slowest_hours, 1),
            "result": "EXCEPTION" if problems else "PASS",
            "reason": "; ".join(problems),
        })
    return results


def save_csv(filename, rows):
    RESULTS_FOLDER.mkdir(exist_ok=True)
    with open(RESULTS_FOLDER / filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    results = check_everyone()
    exceptions = [r for r in results if r["result"] == "EXCEPTION"]

    print(f"Control 7: access removed within {THRESHOLD_HOURS} hours of termination")
    print(f"People checked : {len(results)}")
    print(f"Exceptions     : {len(exceptions)}")
    print(f"Deviation rate : {len(exceptions) / len(results):.1%}")
    print()
    for r in exceptions:
        print(f"  {r['emp_id']}  {r['name']:<16} {r['reason']}")

    save_csv("control7_all_results.csv", results)
    if exceptions:
        save_csv("control7_exceptions.csv", exceptions)
    print()
    print("Saved results to the 'results' folder.")
    sys.exit(1 if exceptions else 0)


if __name__ == "__main__":
    main()

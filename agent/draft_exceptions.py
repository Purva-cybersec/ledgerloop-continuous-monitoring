"""
Step 2: a drafting assistant for control 7 exceptions.

What it does, in order:
  1. Reads the exceptions found by the Step 1 checker.
  2. Builds an "evidence pack" for each one. This is plain code, no AI.
  3. Asks an AI model to DRAFT a finding write-up and a management email,
     using only that evidence and citing it.
  4. Checks the draft with plain code (do the citations exist? do the numbers match?).
  5. Shows the draft to a human, who approves or rejects it.

Nothing is sent anywhere. Approved drafts are saved as files, and every
decision is written to a log.

Usage:
  py agent/draft_exceptions.py --dry-run   (no AI call, no API key needed)
  py agent/draft_exceptions.py             (full run)
  py agent/draft_exceptions.py --only E1292   (just one person; works with --dry-run too)
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Reuse the Step 1 checker's rule and helpers, so there is one source of truth.
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "checks"))
from control7_termination_access import THRESHOLD_HOURS, read_csv, parse_time  # noqa: E402

RESULTS = PROJECT / "results"
DRAFTS = PROJECT / "drafts"
APPROVED = PROJECT / "approved"
LOGS = PROJECT / "logs"

# Which AI model to use. Change this one line to try another.
MODEL = "claude-sonnet-5-5"

# The longest reply the model may write. If a draft is cut off, raise this.
MAX_TOKENS = 4000

SYSTEM_PROMPT = """You help a GRC analyst draft audit exception write-ups.

Rules:
1. Use ONLY the numbered evidence sources provided. After every factual statement, cite the source id in square brackets, like [S2].
2. Never state or guess anything the evidence does not contain. The evidence does NOT say whether the accounts were used after termination, why the delay happened, or who was responsible. Put questions like that in "not_known".
3. Use the exact hour figures shown in the evidence. Do not round them.
4. You are drafting for a human reviewer. Never say that anything has been sent, approved, or confirmed. Do not use gendered pronouns such as he, she, his, or her. Refer to the person by name or as "the employee".
5. Reply with ONLY a JSON object and no other text. It must have exactly these keys:
   "summary": two sentences.
   "criteria": the requirement the control sets, with a citation.
   "condition": what actually happened, with citations.
   "cause": write exactly "Not determined from the evidence provided. Requested from the control owner."
   "effect": the risk this creates, stated only as a possibility, not as a fact.
   "not_known": a list of questions that need answers before this can be finalized.
   "email_subject": a short subject line.
   "email_body": a polite, short email to the control owner. State the facts, then ask for the cause, any compensating evidence, and a remediation plan with a date.
"""

# Words that would claim something the evidence cannot support.
RISKY_WORDS = ["breach", "compromised", "malicious", "was accessed", "were accessed",
               "logged in", "exfiltrat"]


# ---------- Part 1: build the evidence pack (plain code) ----------

def build_evidence(exception_row, terminations, entitlements, removals):
    """Collect the facts for one person and number them S1, S2, S3..."""
    emp_id = exception_row["emp_id"]
    hr = next(t for t in terminations if t["emp_id"] == emp_id)
    terminated = parse_time(hr["termination_time"])
    systems = [e["system"] for e in entitlements if e["emp_id"] == emp_id]
    removal_by_system = {r["system"]: r["removed_time"] for r in removals if r["emp_id"] == emp_id}

    sources = {
        "S1": f"Control 7: terminated users' access must be removed within {THRESHOLD_HOURS} hours of HR termination.",
        "S2": f"HR record: {hr['name']} ({emp_id}), {hr['department']}, terminated {hr['termination_time']}.",
        "S3": f"Accounts held at termination: {', '.join(systems)}.",
    }
    allowed_hours = {float(THRESHOLD_HOURS)}  # numbers the draft is allowed to mention

    number = 4
    for system in systems:
        if system in removal_by_system:
            removed = parse_time(removal_by_system[system])
            hours = round((removed - terminated).total_seconds() / 3600, 1)
            allowed_hours.add(hours)
            sources[f"S{number}"] = (f"{system} removal record: access removed "
                                     f"{removal_by_system[system]}, {hours} hours after termination.")
        else:
            sources[f"S{number}"] = f"{system} removal record: none found."
        number += 1

    sources[f"S{number}"] = f"Automated check result: {exception_row['result']}. {exception_row['reason']}"
    return sources, allowed_hours


# ---------- Part 2: ask the AI model for a draft ----------

def ask_model(sources):
    import anthropic  # imported here so --dry-run works without it installed
    client = anthropic.Anthropic()  # reads the ANTHROPIC_API_KEY environment variable
    evidence_text = "\n".join(f"[{key}] {value}" for key, value in sources.items())
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Evidence:\n{evidence_text}\n\nDraft the exception write-up and the management email.",
        }],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, response.stop_reason


def parse_draft(text):
    """The model should reply with JSON. Tidy it up and turn it into a Python dictionary."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
    return json.loads(cleaned)


# ---------- Part 3: check the draft (plain code) ----------

def verify(draft, sources, allowed_hours):
    """Return a list of warnings. An empty list means nothing suspicious was found."""
    warnings = []

    required = ["summary", "criteria", "condition", "cause", "effect",
                "not_known", "email_subject", "email_body"]
    for key in required:
        if key not in draft:
            warnings.append(f"Missing field: {key}")
    if warnings:
        return warnings

    # Everything except the 'not_known' questions counts as an assertion.
    asserted = " ".join(str(draft[k]) for k in required if k != "not_known")

    cited = set(re.findall(r"\[(S\d+)\]", asserted))
    if not cited:
        warnings.append("The draft contains no citations.")
    for source_id in sorted(cited - set(sources)):
        warnings.append(f"Cites {source_id}, which is not in the evidence.")

    for figure in re.findall(r"(\d+(?:\.\d+)?)\s*hours", asserted):
        if not any(abs(float(figure) - allowed) < 0.05 for allowed in allowed_hours):
            warnings.append(f"The figure '{figure} hours' does not match the evidence.")

    if "not determined" not in str(draft["cause"]).lower():
        warnings.append("The cause field states a cause, but the evidence provides none.")

    lowered = asserted.lower()
    for word in RISKY_WORDS:
        if word in lowered:
            warnings.append(f"Uses '{word}', which the evidence does not support.")

    # The evidence says nothing about anyone's gender, so a pronoun is a guess.
    if re.search(r"\b(he|she|his|her|him|hers)\b", lowered):
        warnings.append("Uses a gendered pronoun, which the evidence does not support.")

    return warnings


# ---------- Part 4: show it to a human and record the decision ----------

def render_markdown(row, draft, warnings, status, note=""):
    lines = [
        f"# Exception draft: {row['name']} ({row['emp_id']})",
        f"**Status: {status}**  {note}",
        "",
    ]
    if warnings:
        lines += ["## Verification warnings"] + [f"- {w}" for w in warnings] + [""]
    else:
        lines += ["## Verification", "No issues found by the automated checks.", ""]
    lines += [
        "## Summary", draft["summary"], "",
        "## Criteria", draft["criteria"], "",
        "## Condition", draft["condition"], "",
        "## Cause", draft["cause"], "",
        "## Effect", draft["effect"], "",
        "## Still unknown",
    ] + [f"- {item}" for item in draft["not_known"]] + [
        "", "## Draft email to control owner",
        f"**Subject:** {draft['email_subject']}", "", draft["email_body"], "",
        "---",
        f"Drafted by an AI model ({MODEL}). Not reviewed or sent until a human approves it.",
    ]
    return "\n".join(lines)


def log_decision(emp_id, warnings, decision, approver):
    LOGS.mkdir(exist_ok=True)
    log_file = LOGS / "agent_log.csv"
    is_new = not log_file.exists()
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "emp_id", "model", "warnings", "decision", "approver"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), emp_id, MODEL,
                         len(warnings), decision, approver])


def review_with_human(row, draft, warnings, approver):
    DRAFTS.mkdir(exist_ok=True)
    APPROVED.mkdir(exist_ok=True)
    draft_text = render_markdown(row, draft, warnings, "DRAFT, NOT APPROVED")
    (DRAFTS / f"{row['emp_id']}_draft.md").write_text(draft_text, encoding="utf-8")

    print("\n" + "=" * 70)
    print(draft_text)
    print("=" * 70)

    while True:
        choice = input("Approve this draft? [y = approve, n = reject, s = skip] ").strip().lower()
        if choice in ("y", "n", "s"):
            break

    if choice == "y":
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        approved_text = render_markdown(row, draft, warnings, "APPROVED",
                                        f"by {approver} on {stamp}")
        (APPROVED / f"{row['emp_id']}_approved.md").write_text(approved_text, encoding="utf-8")
        print("Saved to the 'approved' folder.")
    decision = {"y": "approved", "n": "rejected", "s": "skipped"}[choice]
    log_decision(row["emp_id"], warnings, decision, approver)


# ---------- Putting it together ----------

def main():
    dry_run = "--dry-run" in sys.argv

    exceptions_file = RESULTS / "control7_exceptions.csv"
    if not exceptions_file.exists():
        print("No exceptions file found. Run the checker first:")
        print("  py checks/control7_termination_access.py")
        return

    with open(exceptions_file, newline="") as f:
        exceptions = list(csv.DictReader(f))
    terminations = read_csv("hr_terminations.csv")
    entitlements = read_csv("entitlements.csv")
    removals = read_csv("removals.csv")

    if "--only" in sys.argv and sys.argv.index("--only") + 1 < len(sys.argv):
        wanted = sys.argv[sys.argv.index("--only") + 1]
        exceptions = [row for row in exceptions if row["emp_id"] == wanted]
        if not exceptions:
            print(f"{wanted} is not in the exceptions file.")
            return

    if dry_run:
        sources, _ = build_evidence(exceptions[0], terminations, entitlements, removals)
        print("DRY RUN: no AI call is made. This is exactly what the model would receive.\n")
        print("--- SYSTEM PROMPT ---")
        print(SYSTEM_PROMPT)
        print("--- EVIDENCE PACK (first exception) ---")
        for key, value in sources.items():
            print(f"[{key}] {value}")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("No API key found. Set ANTHROPIC_API_KEY first (see the setup steps).")
        return
    try:
        import anthropic  # noqa: F401
    except ImportError:
        print("The 'anthropic' package is not installed. Run:  py -m pip install anthropic")
        return

    approver = input("Your name (recorded with each decision): ").strip() or "unnamed reviewer"

    for row in exceptions:
        sources, allowed_hours = build_evidence(row, terminations, entitlements, removals)
        print(f"\nDrafting {row['emp_id']} ({row['name']})...")
        raw, stop_reason = ask_model(sources)
        try:
            draft = parse_draft(raw)
        except json.JSONDecodeError:
            # Fail closed: a draft we cannot check is never shown for approval.
            LOGS.mkdir(exist_ok=True)
            raw_file = LOGS / f"{row['emp_id']}_raw_reply.txt"
            raw_file.write_text(raw, encoding="utf-8")
            print("The model's reply was not valid JSON, so it was not shown for approval.")
            if stop_reason == "max_tokens":
                print("Cause: the reply was cut off at the length limit. Raise MAX_TOKENS at the top of the script.")
            else:
                print(f"Stop reason: {stop_reason}.")
            print(f"The raw reply was saved to {raw_file} so you can read it.")
            log_decision(row["emp_id"], ["invalid JSON"], "skipped", approver)
            continue
        warnings = verify(draft, sources, allowed_hours)
        review_with_human(row, draft, warnings, approver)

    print("\nDone. Decisions are recorded in logs/agent_log.csv")


if __name__ == "__main__":
    main()

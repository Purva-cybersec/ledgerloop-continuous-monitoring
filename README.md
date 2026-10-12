# LedgerLoop Continuous Monitoring

Turning controls into code. This project takes controls from my [SOC 2 Type II simulation](https://github.com/Purva-cybersec/soc2-type2-audit-simulation) and checks them automatically against **every record**, instead of a sample. It is built step by step; this is a work in progress.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Python checker for control 7 (terminated users' access removed within 24 hours) | Done |
| 1b | Run the checker automatically in GitHub Actions, on every change and daily | Done |
| 1c | Scan Terraform with Checkov in the pipeline, with two checks tied to controls 10 and 18 | Done |
| 2 | AI assistant that drafts exception write-ups, with a human approving | Done |
| 3 | Questionnaire assistant that answers from policy, with citations | Planned |

## About the red X

The check in GitHub Actions is expected to fail. The simulated data contains
four planted exceptions for control 7, so the pipeline reports a failure, which
is the control working as designed. A real pipeline would alert the control
owner in the same way.

The Terraform scan shows the same idea in both directions: its first run failed
on an insecure storage definition, and the next run passed after the fix.

## Run it

**Step 1: the checker.** Only Python 3.9 or newer is needed. No extra packages.

```
python checks/control7_termination_access.py
```

**Step 2: the drafting assistant.**

```
python -m pip install anthropic
python tests/test_agent_checks.py            # guardrail tests, no API key needed
python agent/draft_exceptions.py --dry-run   # shows what the model would receive, no key needed
python agent/draft_exceptions.py             # full run, needs an API key
```

The full run reads an API key from the `ANTHROPIC_API_KEY` environment variable.
The key is never stored in the code or the repository. On Windows, use `py`
instead of `python` if `python` is not recognized.

## How it works (Step 1)

1. `data/hr_terminations.csv` holds the HR termination records (the system of record).
2. `data/entitlements.csv` lists which systems each person had an account in (Okta, AWS, GitHub).
3. `data/removals.csv` holds when each account was removed.
4. The checker joins the three, applies the 24-hour rule, and writes `results/control7_all_results.csv` and `results/control7_exceptions.csv`.

## Step 2: drafting assistant

For each exception the checker finds, plain code builds a numbered evidence pack,
an AI model drafts a finding write-up and a management email that cites that
evidence, plain code verifies the draft, and a human approves or rejects it.
Every decision is logged.

**What the automated checks catch:** citations that don't exist, hour figures that
don't match the evidence, a stated cause when none is known, claims like "breach"
that the evidence doesn't support, and gendered pronouns.

**What found real problems:** during human review I noticed the model kept
assuming gender. I added a rule to the prompt, a deterministic check in code,
and a test. Separately, one draft failed to parse, most likely because the
reply was cut off at the length limit. The script now saves the raw reply of any
failed draft, reports whether it was cut off, and allows longer replies.

**Design choices:** code gathers and verifies, the AI only reads and drafts, and
the human decides. A draft that cannot be checked is never shown for approval
(it fails closed). See `examples/` for sample approved drafts and the decision log.

## Repository contents

```
├── checks/control7_termination_access.py   Step 1 checker
├── agent/draft_exceptions.py               Step 2 drafting assistant
├── tests/test_agent_checks.py              Tests for the draft verifier
├── data/                                   Simulated HR, entitlement, and removal exports
├── terraform/storage.tf                    Simulated storage definition, scanned by Checkov
├── examples/                               Sample approved drafts and decision log
└── .github/workflows/                      Control 7 check, Terraform scan, agent tests
```

## Limits, stated plainly

- **All data is simulated** and derived from the population in the SOC 2 simulation. No real company data is used.
- **No live connections.** The checker reads exported files. A production version would pull from the HR, Okta, AWS, and GitHub APIs.
- **Identity matching is simplified.** Records are joined on employee ID. Real systems often identify the same person differently (work email, username, service account), which is a harder problem this version does not solve.
- **The automated draft checks catch some errors, not all.** A fluent but wrong sentence with a valid citation could pass, which is why a human approves every draft. Drafts also vary from run to run.
- **Citation tags in the emails are for the reviewer** and would be removed before anything is sent.
- **Real data would need a vendor review.** Sending actual employee records to an AI provider would itself be a third-party risk decision. Here the data is invented.
- **A learning project**, not a replacement for GRC platforms such as Vanta or Drata.

# Exception draft: Marco Tan (E1131)
**Status: APPROVED**  by Purva on 2026-10-12 12:40

## Verification
No issues found by the automated checks.

## Summary
Control 7 requires terminated users' access to be removed within 24 hours of HR termination, and the automated check returned an EXCEPTION for Marco Tan (E1131) [S1][S7]. The okta and aws accounts were each removed 74.5 hours after termination, while the github account was removed 11.6 hours after termination [S4][S5][S6].

## Criteria
Control 7 requires that terminated users' access be removed within 24 hours of HR termination [S1].

## Condition
HR records show Marco Tan (E1131), Product, was terminated on 2026-04-01 at 17:47 [S2]. The employee held okta, aws, and github accounts at termination [S3]. The okta access was removed on 2026-04-04 at 20:17, 74.5 hours after termination [S4]. The aws access was removed on 2026-04-04 at 20:17, 74.5 hours after termination [S5]. The github access was removed on 2026-04-02 at 05:25, 11.6 hours after termination [S6]. The automated check returned EXCEPTION for okta (removed after 74.5 hours) and aws (removed after 74.5 hours) [S7].

## Cause
Not determined from the evidence provided. Requested from the control owner.

## Effect
Because the okta and aws accounts remained active beyond the 24-hour requirement, there is a possibility that the accounts could have been used by the former employee or by someone else during that period, and that the organization's systems or data could have been exposed to unauthorized access. The evidence provided does not show whether any such use occurred.

## Still unknown
- Were the okta and aws accounts used or accessed at any time after the termination time of 2026-04-01 17:47?
- Why were the okta and aws accounts removed 74.5 hours after termination, while the github account was removed 11.6 hours after termination?
- Who was responsible for performing and monitoring the access removals, and when was the removal request raised?
- Is there compensating evidence (for example, logs showing no activity, or other restrictions that blocked sign-in) covering the period between termination and removal?
- Is this an isolated case, or have other terminations been affected by the same delay?
- What remediation plan, and target completion date, will the control owner put in place?

## Draft email to control owner
**Subject:** Control 7 exception: delayed access removal for E1131 (okta, aws)

Hello,

During our review of Control 7, which requires terminated users' access to be removed within 24 hours of HR termination [S1], the automated check returned an exception for Marco Tan (E1131) [S2][S7].

HR records show the termination took place on 2026-04-01 at 17:47 [S2]. The employee held okta, aws, and github accounts at that time [S3]. The okta and aws access were both removed on 2026-04-04 at 20:17, 74.5 hours after termination [S4][S5]. The github access was removed on 2026-04-02 at 05:25, 11.6 hours after termination [S6].

To help us finalize the write-up, could you please provide:
1. The cause of the delay in removing the okta and aws access.
2. Any compensating evidence, such as activity logs for the okta and aws accounts covering the period between termination and removal.
3. A remediation plan, including a target completion date.

Thank you for your help. Please let us know if you would like to discuss any of this.

Kind regards,
[Analyst name]

---
Drafted by an AI model (claude-sonnet-5-5). Not reviewed or sent until a human approves it.
# Exception draft: Omar Hughes (E1068)
**Status: APPROVED**  by Purva on 2026-10-12 12:44

## Verification
No issues found by the automated checks.

## Summary
Control 7 requires terminated users' access to be removed within 24 hours of HR termination [S1]. For Omar Hughes (E1068), okta and github access were removed in time, but no removal record was found for aws, and the automated check returned an EXCEPTION [S4][S6][S5][S7].

## Criteria
Terminated users' access must be removed within 24 hours of HR termination [S1].

## Condition
Omar Hughes (E1068), Engineering, was terminated on 2026-04-22 at 19:29 [S2]. The employee held okta, aws, and github accounts at termination [S3]. The okta access was removed on 2026-04-23 at 03:17, 7.8 hours after termination [S4]. The github access was removed on 2026-04-22 at 21:58, 2.5 hours after termination [S6]. No aws removal record was found [S5]. The automated check returned EXCEPTION for aws: no removal record, access may still be active [S7].

## Cause
Not determined from the evidence provided. Requested from the control owner.

## Effect
If the aws access has not been removed, a former employee could possibly still have access to that environment, and the 24-hour requirement in Control 7 would not have been met for that account [S1][S5][S7]. Whether this has resulted in any actual exposure cannot be stated from the evidence.

## Still unknown
- Is the aws access for Omar Hughes (E1068) still active, or was it removed without a record being created?
- Was the aws account used at any time after the 2026-04-22 19:29 termination?
- Why is there no aws removal record, and why did the automated check flag it?
- Are there compensating controls or other evidence (for example, an aws console or IAM log) showing the access was disabled or unusable?
- If the access is still active, when will it be removed?
- Which team or process owns aws access removal for terminated users?

## Draft email to control owner
**Subject:** Control 7 exception: no aws removal record for terminated user E1068

Hello,

During our review of Control 7, which requires terminated users' access to be removed within 24 hours of HR termination [S1], we noted an exception for Omar Hughes (E1068), Engineering, who was terminated on 2026-04-22 at 19:29 [S2].

The employee held okta, aws, and github accounts at termination [S3]. The okta access was removed 7.8 hours after termination [S4], and the github access was removed 2.5 hours after termination [S6]. We found no removal record for aws [S5], and our automated check flagged that the aws access may still be active [S7].

Could you please provide:
1. The cause of the missing aws removal record.
2. Any compensating evidence, such as logs showing the aws access was disabled or was not used after termination.
3. A remediation plan with a target completion date.

Thank you for your help. Please let us know if you have any questions.

Kind regards,
[Analyst name]

---
Drafted by an AI model (claude-sonnet-5-5). Not reviewed or sent until a human approves it.
# AtlasBridge Services — customer onboarding AS-IS brief

## Business context

AtlasBridge Services is a fictional business-services provider onboarding eight
new customers per business day. The public demonstration focuses only on the
journey from receipt of an onboarding request to account activation and customer
notification.

## Current-state problem

The same identity and company information is entered first by Intake and then
re-keyed by an Onboarding Analyst into the CRM. Document validation, compliance
screening, and risk review are performed largely in sequence. Work waits in
separate queues, while no single role owns the complete case from intake through
activation.

Exceptions are resolved by different roles depending on who notices the issue.
Missing documents normally return to Onboarding, data mismatches may return to
Intake or remain with Onboarding, and sanctions false positives go to
Compliance. This variation is not visible to the customer and does not have a
single service-level owner.

Account activation is technically performed by a system step, but the evidence
that all required checks were completed is not attached consistently to the
activation record. The process therefore has both an efficiency problem and a
control-evidence problem.

## Decision to support

Which future process offers the best measurable trade-off across customer speed,
first-pass quality, labor cost, control preservation, implementation effort, and
change risk?

## Scope boundaries

Included: intake, CRM entry, document validation, compliance screening, risk
review, exception resolution, activation, notification, queue time, touch time,
synthetic labor cost, handoffs, rework, and control evidence.

Excluded: pricing, sales qualification, contract negotiation, payment, live
identity providers, production workflow automation, workforce reduction,
calendar-time forecasting, and legal or regulatory interpretation.

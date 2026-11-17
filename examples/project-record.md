# Illustrative project design record

This is synthetic training material. It does not describe a real customer, actual user research, or verified software.

## Product understanding

- **Person and situation:** an equipment-desk operator recording returned rental items.
- **Task:** identify a rental, inspect its returned items, and record the return or an exception.
- **Observable outcome:** the system records the selected items and shows the resulting rental state.
- **Objects:** rental, item, return, condition, exception.
- **Source/status:** proposed brief for this example; no implementation has been inspected.

## Behavior to preserve

Inspect the actual system before filling this section. Candidate areas to investigate include partial returns, item identity, authorization, and the existing save contract. None is asserted as verified here.

## Screen commitments

| Need | Screen question | Visible affordance | Proposed action/state | Evidence needed |
|---|---|---|---|---|
| Identify the rental | Am I processing the correct transaction? | Rental identifier and relevant distinguishing context | Select the intended rental | Contract/source comparison and observed selection |
| Record returned items | Which items are being returned now? | Explicit item selection and condition controls | Submit selected items | Exercised success and recovery paths |
| Understand completion | What was recorded and what remains outstanding? | Result summary with remaining items | Continue or return to the queue | Current rendered result and actual resulting state |

## Working visual recommendation

Use a compact, readable workspace with a stable rental context and clear item-level decisions. Give errors and unresolved items enough emphasis to support the operator's task. This is a recommendation, not a user-approved direction.

## Review status

Intent, task completion, visual craft, accessibility checks, responsiveness, and behavior preservation are all **not tested**. This document is a proposal and supplies no evidence of implementation quality.

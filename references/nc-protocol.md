# The `NEED_CLARIFICATION` (NC) Protocol

This specification defines the formal ambiguity-tracking mechanism for the `enterprise-product` engineering operating system. Ambiguity must never be resolved by guessing or inventing unverified assumptions.

---

## 1. Core Principles of Ambiguity Handling

1. **Ambiguity is Recorded, Not Invented**: When an AI agent or engineer encounters missing domain specifications, conflicting business requirements, or incomplete API contracts, it is strictly forbidden to guess. The gap must be recorded as a formal `NEED_CLARIFICATION` (NC) item.
2. **Deterministic Tracking**: Every NC item is tracked as an individual artifact with a stable unique identifier.
3. **The 14-Day Merge Escalation Gate**: Any open NC item that remains unresolved after 14 calendar days mechanically blocks Pull Request merges for affected projects.

---

## 2. NC Item Schema

Every NC item must be authored using `templates/NEED_CLARIFICATION.template.md` and placed in `docs/nc/` or within the project's documentation folder:

```markdown
---
id: "NC-20261012-001"
status: "OPEN"                        # OPEN | RESOLVED | ABANDONED
created_date: "2026-10-12"
resolved_date: null
discovered_by: "agent-antigravity"
severity: "blocking"                 # blocking | non-blocking
affected_projects:
  - "services/order-service"
  - "libs/core-contracts"
---

# NEED_CLARIFICATION: Order Cancellation Refund Window

## 1. Context & Trigger
During implementation of the order cancellation workflow in `services/order-service`, the business requirement states that users may cancel orders within 30 minutes of placement. However, it does not specify whether payment gateway processing fees are refunded or deducted from the customer's balance.

## 2. Unresolved Question
Should the payment gateway fee ($0.30 + 2.9%) be refunded to the customer or absorbed by the merchant when an order is cancelled within the 30-minute grace window?

## 3. Options Considered
- **Option A (Full Refund)**: Refund 100% of the charge. Merchant absorbs gateway fee.
  - *Pros*: Superior customer experience, aligns with standard e-commerce expectations.
  - *Cons*: Merchant incurs direct financial loss on cancellations.
- **Option B (Deduct Fee)**: Refund charge minus non-refundable gateway fee.
  - *Pros*: Zero fee loss for merchant.
  - *Cons*: High customer friction, potential chargeback disputes.
- **Option C (Store Credit)**: Issue 100% refund as store credit, cash refund deducts fee.
  - *Pros*: Encourages repeat purchases, mitigates gateway fee loss.
  - *Cons*: Requires store credit accounting subsystem.

## 4. Resolution & Decision
[Pending human product owner response]

## 5. Escalation Log
- 2026-10-12: Item created during Phase 1 analysis of Order Cancellation feature.
```

---

## 3. The 14-Day Aging & Escalation Lifecycle

```text
Day 0: Discovery & NC Creation (Status: OPEN)
  │
  ├──► Days 1–13: Open Item Active
  │    - Team works on resolution
  │    - PRs affecting non-blocked paths can proceed
  │
  └──► Day 14+: 14-DAY MERGE BLOCK TRIGGERED
       - Mechanical check: scripts/check-nc-items.py --max-age 14 flags failure
       - CI fails with exit code 1
       - PRs affecting declared projects are halted
       - PR label blocked/nc attached
       - Escalated to Product Owner / Principal Architect
```

### Mechanical Enforcement
In the CI workflow and during the 2-Pass PR Self-Audit, the script executes:
```bash
python3 scripts/check-nc-items.py --max-age 14 --dir docs/nc
```
- If an item with `status: OPEN` has a `created_date` older than 14 days, the script exits with code `1` and prints the blocking item IDs and affected projects.
- Pull Requests cannot be merged automatically or manually until the item is resolved or deferred with an accepted ADR.

---

## 4. Resolution Workflow

To resolve an NC item:
1. Update `status: "RESOLVED"`.
2. Populate `resolved_date: "YYYY-MM-DD"`.
3. Fill Section 4 with the rationale, selected option, and approving stakeholder.
4. If the decision alters architecture or Tier 2 defaults, link to a new or updated ADR.
5. Commit the resolution to the repository. The merge block is immediately lifted.

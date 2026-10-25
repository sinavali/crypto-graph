<!-- AUTO-GENERATED FROM AGENT.md by ep manifest sync -->

---
project_name: "blockchain-contracts"
profile: "D"
stack: "python"
scope: "shared"
owner: "engineering"
tier_overrides: []
dr:
  rto: "1h"
  rpo: "15m"
slo:
  tier: "tier-1"
  availability_target: "0.999"
resources:
  cpu_limit: "500m"
  memory_limit: "512Mi"
---

# Project Agent Manifest: blockchain-contracts

## 1. Scope & Business Intent
Shared domain contracts, Pydantic schemas, multi-chain address normalizers, and deterministic offline test fixtures.

## 2. Architectural Profile & Boundaries
- **Profile**: D (Shared Contracts & Core Libraries)
- **Primary Inputs**: None (Library).
- **Allowed Outbound Dependencies**: Standard library and Pydantic.
- **Forbidden Dependencies**: Persistence frameworks, UI frameworks, or network clients.

## 3. Local Nx Target Delegations
- `nx lint blockchain-contracts`
- `nx test blockchain-contracts`
- `nx build blockchain-contracts`
- `nx audit blockchain-contracts`

## 4. Test & Verification Rules
- 100% pure unit tests, zero external I/O, deterministic fixtures.
- Domain coverage target $\ge 95\%$.

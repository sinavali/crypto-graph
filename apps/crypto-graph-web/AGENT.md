---
project_name: "crypto-graph-web"
profile: "B"
stack: "ts"
scope: "frontend"
owner: "engineering"
tier_overrides: []
dr:
  rto: "1h"
  rpo: "15m"
slo:
  tier: "tier-1"
  availability_target: "0.999"
resources:
  cpu_limit: "1000m"
  memory_limit: "1Gi"
---

# Project Agent Manifest: crypto-graph-web

## 1. Scope & Business Intent
Domain responsibility and business purpose of crypto-graph-web.

## 2. Architectural Profile & Boundaries
- **Profile**: B
- **Primary Inputs**: Internal domain events, API clients.
- **Allowed Outbound Dependencies**: `libs/core-contracts`
- **Forbidden Dependencies**: Direct cross-boundary domain couplings.

## 3. Local Nx Target
- `nx lint crypto-graph-web`
- `nx test crypto-graph-web`
- `nx build crypto-graph-web`
- `nx audit crypto-graph-web`

## 4. Test & Verification Rules
- Real ephemeral container verification for databases.
- Domain coverage target $\ge 95\%$, adapter coverage $\ge 80\%$.

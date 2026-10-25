<!-- AUTO-GENERATED FROM AGENT.md by ep manifest sync -->

---
project_name: "crypto-graph-web"
profile: "B"
stack: "python"
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
FastAPI + Jinja2 SSR + HTMX server-rendered web presentation layer with interactive Cytoscape.js canvas visualizer.

## 2. Architectural Profile & Boundaries
- **Profile**: B (Web Applications - Pure Python SSR)
- **Primary Inputs**: User HTTP requests, HTMX partial queries.
- **Allowed Outbound Dependencies**: `services/crypto-graph-api`, `libs/blockchain-contracts`
- **Forbidden Dependencies**: Direct database manipulation outside designated application services.

## 3. Local Nx Target Delegations
- `nx lint crypto-graph-web`
- `nx test crypto-graph-web`
- `nx build crypto-graph-web`
- `nx audit crypto-graph-web`

## 4. Test & Verification Rules
- Component and template rendering tests via pytest and Starlette TestClient.
- Sub-2.5s render response with progressive graph loading.

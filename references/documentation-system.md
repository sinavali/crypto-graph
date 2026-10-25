# Enterprise Documentation System

This specification incorporates and elevates the core documentation capabilities into the `enterprise-product` engineering system. Documentation is an active, machine-verifiable contract that leads code implementation.

---

## 1. The Core Doctrine: Docs Lead, Code Follows

In an enterprise monorepo, code is never written into a void:
```text
1. Change Request / Task
     │
     ▼
2. Impact Graph Analysis (Trace affected projects, contracts, dependencies)
     │
     ▼
3. CHANGE SURFACE Declaration (`CHANGE_SURFACE.md`)
     │
     ▼
4. Mechanical Validation (`python3 scripts/validate-change-surface.py`)
     │
     ▼
5. Implementation & Value-Driven Tests (Red -> Green -> Refactor)
     │
     ▼
6. 2-Pass PR Self-Audit vs CHANGE SURFACE
```

No non-trivial modification to code, configuration, or contracts is permitted without an approved, validated **Change Surface**.

---

## 2. The Change Surface Specification

A Change Surface bounds the scope of work, prevents scope creep, and informs reviewers of the exact blast radius.

### 2.1 Change Surface Schema & Storage Paths
To prevent branch collision across concurrent features, a Change Surface may be stored in one of two supported formats:
1. **Versioned Archive Path (Recommended)**: `docs/changes/YYYYMMDD-<branch-slug>.md`
2. **Local Root Staging**: `CHANGE_SURFACE.md` (at repo root, or symlinked)
3. **PR Embedded Contract**: Formatted directly within the Pull Request description matching `templates/PR_CONTRACT.template.md`.

Every Change Surface must declare:
1. **Metadata**: Title, author/agent, created date, target branch, risk level.
2. **Intent & Problem Statement**: Precise business rationale and problem description.
3. **Affected Projects**: Monorepo packages affected (`apps/*`, `services/*`, `libs/*`) and their Architectural Profiles.
4. **Code Surface**: Explicit list of files and code symbols (classes, functions, interfaces) targeted for addition or modification.
5. **Test Surface**: Exact test files and suites verifying the change (Unit, Ephemeral Container Integration, Failure paths).
6. **Invariants Preserved**: Core business rules and architectural constraints that must remain unbroken (including Tier 1 Inviolables and structural limits).
7. **Risk Matrix & Rollback Strategy**: Identified risks, blast radius, and recovery plan.

### 2.2 Mechanical Validation
The script `scripts/validate-change-surface.py` verifies:
- Presence of all required sections.
- Non-empty Code Surface and Test Surface.
- Existence of affected project references within the monorepo.
- Prevention of unconstrained wildcards (`*`) without path scoping.
- Resolves files at root (`CHANGE_SURFACE.md`) or within `docs/changes/`.

---

## 3. Architecture Decision Records (ADRs)

An ADR captures an important architectural decision, along with its context, alternatives considered, and consequences.

### 3.1 When is an ADR Mandatory?
An ADR must be created in `docs/adr/NNNN-<slug>.md` whenever a change:
1. Deviates from a **Tier 2 Strong Default** (e.g., altering coverage thresholds, waiving a port-adapter interface).
2. Introduces a new database, message broker, cloud service, or external protocol.
3. Alters the architectural profile of a project (e.g., transitioning from Profile B to Profile A).
4. Deprecates or introduces a major breaking change to shared API contracts (Profile D).
5. Modifies core cross-cutting patterns (authentication, distributed tracing, encryption).

### 3.2 ADR Structure
Every ADR conforms to `templates/ADR.template.md` and contains:
- Number, Title, Date, Status (`Proposed`, `Accepted`, `Superseded`, `Rejected`).
- Context & Problem Statement.
- Decision Drivers & Constraints.
- Considered Options & Trade-Offs.
- Decision Outcome & Justification.
- Positive, Negative, and Neutral Consequences.
- Compliance & Verification Plan.

---

## 4. File-Level Documentation & Inline Standards

- **Two Audiences, Two Files**:
  - `README.md`: Written for human developers; covers onboarding, architecture overview, and developer commands.
  - `AGENT.md`: Written for AI agents; specifies strict machine-readable rules, invariants, and local toolchain targets.
- **Complex Domain Logic**: For complex state machines, cryptographic algorithms, or financial calculation modules, code comments must explain *why* an invariant exists, not just *what* the syntax does.
- **Companion Documentation (`<filename>.md`)**: If a domain aggregate root requires extensive documentation exceeding reasonable file headers, place a companion markdown document alongside it (`order_aggregate.md`) referencing domain specifications.

---

## 5. Documentation Drift Detection

Documentation drift is treated as a software defect during audits:
- If a pull request modifies domain interfaces, data schemas, or configuration without updating the corresponding documentation, Dimension 9 of the Enterprise Audit will flag a `blocking` finding.
- The CI pipeline runs doc validation checks to ensure all links and ADR numbers are strictly monotonic and unbroken.

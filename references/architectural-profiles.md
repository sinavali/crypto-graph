# Enterprise Architectural Profiles

Every project in the monorepo must be assigned to one of four architectural profiles in its `AGENT.md`. This document establishes the concrete rules, folder layouts, allowed dependencies, and forbidden patterns for each profile.

---

## Profile A: Backend & Core Services (DDD + Hexagonal Architecture)

Profile A governs backend microservices, monolithic cores, background workers, and CLI applications (e.g., Go, C# / .NET, Rust, Node.js/TypeScript, PHP/Laravel, Python).

### 1. Architectural Model: Ports and Adapters
All application logic is organized into three concentric rings:

```text
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer (Primary & Secondary Adapters)         │
│  HTTP Controllers, gRPC Servers, DB Repositories, Kafka/AMQP│
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Application / Use-Case Layer                         │  │
│  │  Command Handlers, Query Handlers, Ports (Interfaces) │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Domain Layer (Pure Core)                       │  │  │
│  │  │  Entities, Value Objects, Domain Events, Rules  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Dependency Inversion Rules
- **The Domain Rule**: The Domain Layer has **zero dependencies** on outer layers, external frameworks, ORMs, HTTP libraries, or cloud SDKs.
- **The Application Rule**: Depends only on Domain. Declares Primary Ports (inbound interfaces) and Secondary Ports (outbound interfaces for persistence, messaging, clock).
- **The Infrastructure Rule**: Implements Secondary Ports (e.g., `PostgresUserRepository` implements `UserRepositoryPort`) and triggers Primary Ports (e.g., `ExpressUserController` invokes `CreateUserUseCase`).

### 3. Canonical Directory Layout
```text
services/<service-name>/
├── project.json                      # Nx project configuration
├── AGENT.md                          # Profile A manifest
├── src/
│   ├── domain/                       # Pure Domain Layer
│   │   ├── entities/                 # Aggregate roots, entities with private state & invariants
│   │   ├── value-objects/            # Immutable value objects with validation
│   │   ├── events/                   # Pure domain event definitions
│   │   └── exceptions/               # Domain-specific business rule exceptions
│   ├── application/                  # Application Layer
│   │   ├── ports/
│   │   │   ├── inbound/              # Use-case interfaces (commands/queries)
│   │   │   └── outbound/             # Repository, event-publisher, clock interfaces
│   │   ├── use-cases/                # Orchestrators of domain models
│   │   └── dto/                      # Input/Output DTOs for use cases
│   └── infrastructure/               # Infrastructure Layer
│       ├── adapters/
│       │   ├── primary/              # Web controllers, CLI handlers, message consumers
│       │   │   ├── http/
│       │   │   └── grpc/
│       │   └── secondary/            # Database implementations, external API clients, clock
│       │       ├── persistence/
│       │       └── messaging/
│       └── config/                   # Dependency injection, environment parsing
└── tests/
    ├── unit/                         # Pure domain & use-case unit tests (Fast, no I/O)
    ├── integration/                  # Ephemeral container tests (PostgreSQL/Redis/Kafka)
    └── contract/                     # Pact or schema verification tests
```

### 4. Distributed Resilience & Transactional Integrity
- **Transactional Outbox Pattern**: In distributed event-driven systems, use cases that mutate aggregate state and emit domain events must persist the event to a local transactional `outbox_events` table (see `templates/outbox-migration.sql`) within the same ACID database transaction. Direct in-memory publishing to network message brokers without an outbox is strictly forbidden for non-idempotent operations.
- **Idempotency Keys**: All mutating ingress boundaries (REST controllers, gRPC handlers, message consumers) must accept and enforce an idempotency key with TTL deduplication.
- **Graceful Shutdown**: Servers must trap `SIGTERM`/`SIGINT`, stop accepting new inbound connections, drain active HTTP/gRPC requests within a configured grace period (15–30s), finish processing active queue messages, and cleanly close database connection pools.

### 5. Idiomatic Language DDD Directives
- **Go DDD Invariants**:
  - Pure domain packages have unexported struct fields; state mutations must pass through constructor functions (`NewOrder(...) (*Order, error)`) and aggregate methods (`func (o *Order) Cancel(...) error`).
  - Interfaces must be defined at the **consumer/use-case site**, not at the producer site.
  - Domain errors must be typed package variables or custom structs (`var ErrOrderAlreadyShipped = errors.New(...)`). Zero naked string errors.
- **Rust DDD Invariants**:
  - Use algebraic data types (`enum OrderStatus`) to make invalid domain states unrepresentable at compile time.
  - Value objects use the newtype pattern: `struct OrderId(Uuid); struct Money(u64, Currency);`.
  - All mutating domain methods must return `Result<(), DomainError>`.

### 6. Forbidden Patterns in Profile A
- **Anemic Domain Models**: Entities acting as plain property bags with external procedural logic modifying state directly. Invariants must be guarded inside entities.
- **Leaking ORM Entities into Domain**: Exposing Hibernate/Prisma/Entity Framework/Eloquent/GORM models as domain models. Persistence models must map to domain entities.
- **Engine-Substitution Mocks in Integration Tests**: Substituting PostgreSQL/MySQL with in-memory SQLite in tests. (Using SQLite in tests is permitted only if SQLite is the actual production engine). Must use Testcontainers or Podman.
- **Ambient Time Calls**: Calling `DateTime.Now`, `time.Now()`, `Date.now()` inside domain or use-cases. Must inject a `ClockPort`.
- **Framework Attributes/Annotations on Domain Types**: ORM annotations (`@Table`, `@Column`, `[Table]`) inside pure domain models.

---

## Profile B: Web Applications (SSR, SSG, SPA)

Profile B governs server-side rendered (SSR), static (SSG), and single-page (SPA) enterprise web applications across any web framework (React, Next.js, Vue, Nuxt, Angular, Svelte, SvelteKit, Astro, Solid, HTMX).

### 1. Architectural Model: Clean Component & State Layering
Web applications decouple presentation, state machines, and data access into distinct layers:

```text
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (Atomic / Composable UI Components)     │
│  Pure renderers, zero business logic, WCAG 2.2 AA compliant │
├─────────────────────────────────────────────────────────────┤
│  Feature & State Layer (Hooks / Stores / View-Models)       │
│  State transitions, optimistic updates, view-models         │
├─────────────────────────────────────────────────────────────┤
│  Domain & Contract Client Layer (Typed API Clients, DTOs)   │
│  Runtime schema validation (Zod/Valibot), OpenAPI clients   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Canonical Directory Layout
```text
apps/<web-app-name>/
├── project.json                      # Task orchestrator configuration
├── AGENT.md                          # Profile B manifest
├── src/
│   ├── routes/                       # Routing & page entrypoints (app/, pages/, or routes/)
│   ├── components/                   # Reusable UI Components
│   │   ├── ui/                       # Primitive design system components (buttons, dialogs)
│   │   └── feedback/                 # Error boundaries, loading states, empty states
│   ├── features/                     # Cohesive feature slices
│   │   └── <feature-name>/
│   │       ├── components/           # Feature-specific composition widgets
│   │       ├── hooks/                # Feature state logic, queries & mutations
│   │       └── state/                # Store slices / state machines
│   ├── contracts/                    # Auto-generated API client & runtime schema validators
│   └── lib/                          # Framework utilities, telemetry, auth session
└── tests/
    ├── unit/                         # Component and state logic unit tests
    ├── e2e/                          # Critical user journey tests (Playwright/Cypress)
    └── a11y/                         # Automated accessibility test suite (Axe-core)
```

### 3. Non-Negotiable Mandates
- **SSR Hydration Safety**: No window/document access during SSR execution. Zero hydration mismatch errors.
- **Accessibility (WCAG 2.2 AA)**: Interactive elements must have accessible labels, full keyboard navigation, and proper ARIA semantics. Automated Axe-core tests are mandatory in the project's test suite.
- **Bundle Budgets**: Enforce initial bundle size budgets ($\le 180 \text{ KB}$ gzipped for critical entrypoints).
- **Design Tokens & Aesthetic Hygiene**:
  - All styling must consume a centralized token system: 4–6 semantic color hexes, clear typographic scale, consistent spacing steps.
  - Ban generic AI clichés: tracked-out all-caps labels, monolithic card grids, artificial gradient washes, and non-semantic numbered badges (01/02/03).
- **Fluid Motion & Direct Manipulation**:
  - Interactions respond on pointer-down, not click-up.
  - 1:1 direct touch/mouse tracking via Pointer Events with `setPointerCapture`.
  - Spring-driven animations inheriting release velocity with interruptible, non-blocking physics.
- **Zero-Trust Web Security**: Strict Content Security Policy (CSP), sanitized outputs against XSS, HTTP-only secure cookies for tokens, anti-CSRF protection on mutating requests.

### 4. Forbidden Patterns in Profile B
- **Direct API Fetches inside Presentation Components**: Components must receive data through feature hooks, view-models, or props.
- **Missing Loading/Error/Empty States**: Every dynamic view must implement explicit visual states for Loading, Empty, Success, and Error.
- **Unvalidated External Data**: Parsing API responses using `any` or untyped casts without runtime schema validation.
- **Inline Styles & Ad-Hoc CSS**: Arbitrary inline color hexes and margins bypassing design tokens.

---

## Profile C: Mobile Clients (Native iOS, Android, and Cross-Platform)

Profile C governs mobile applications across all platforms and toolchains: Native iOS (Swift/SwiftUI), Native Android (Kotlin/Jetpack Compose), Flutter (Dart), React Native (TypeScript), and Kotlin Multiplatform (KMP).

### 1. Architectural Model: Clean Mobile Architecture & Unidirectional State Flow
Separation of native UI views from reactive state machines and encrypted persistence:

```text
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (Native Views, Screens, Navigation)     │
│  Zero business calculations; binds strictly to state streams│
├─────────────────────────────────────────────────────────────┤
│  State Machine Layer (BLoC / MVI / Redux / View-Models)     │
│  Unidirectional data flow, offline-first queue, lifecycle   │
├─────────────────────────────────────────────────────────────┤
│  Domain Layer (Entities, Use Cases, Repository Contracts)   │
│  Pure language logic, zero UI framework dependencies        │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (Repositories, Encrypted DB, REST/gRPC Clients) │
│  Hardware encryption, offline synchronization, caching      │
└─────────────────────────────────────────────────────────────┘
```

### 2. Canonical Directory Layout
```text
apps/<mobile-app-name>/
├── project.json                      # Task orchestrator configuration
├── AGENT.md                          # Profile C manifest
├── lib/ (or src/ for Native / React Native)
│   ├── core/                         # Network clients, encrypted storage, error handling
│   │   ├── error/
│   │   ├── network/
│   │   └── storage/                  # Hardware secure storage wrapper (Keychain/KeyStore/SQLCipher)
│   ├── features/
│   │   └── <feature-name>/
│   │       ├── data/
│   │       │   ├── datasources/      # Remote (REST/gRPC) & Local (Encrypted DB)
│   │       │   ├── models/           # Serialization models & DTOs
│   │       │   └── repositories/     # Repository implementations
│   │       ├── domain/
│   │       │   ├── entities/         # Pure business domain models
│   │       │   ├── repositories/     # Repository interfaces
│   │       │   └── usecases/         # Callable business use cases
│   │       └── presentation/
│   │           ├── state/            # State machines (BLoC / Cubit / View-Models)
│   │           ├── screens/          # Top-level screen views
│   │           └── components/       # Reusable mobile UI components
│   └── main.*                        # Application entrypoint
└── tests/
    ├── unit/                         # Use case & state machine transition tests
    ├── ui/                           # Screenshot golden tests & widget/view interaction tests
    └── integration/                  # Mock server / containerized backend tests
```

### 3. Non-Negotiable Mandates
- **Hardware-Backed Encrypted Storage**: Sensitive data, access tokens, and local offline databases must be encrypted using platform hardware enclaves (iOS Keychain, Android KeyStore, SQLCipher).
- **Offline-First Synchronization**: Mutating operations must queue securely when offline with idempotent conflict resolution.
- **Battery & Lifecycle Awareness**: Timers, location listeners, and background sync streams must pause on app backgrounding and resume cleanly.

### 4. Forbidden Patterns in Profile C
- **Business Logic in View Lifecycle**: Mutating domain state directly inside platform view life-cycles or UI widgets.
- **Raw Unencrypted Local Storage**: Using plaintext SQLite, shared preferences, or unencrypted local storage for user/enterprise data.
- **UI Framework Imports into Domain Layer**: Domain entities and use cases must be pure language types with zero UI framework imports (`UIKit`, `SwiftUI`, `android.view`, `package:flutter`, `react-native`).
- **Hardcoded Screen Dimensions**: Bypassing responsive and adaptive layouts across device form factors.

---

## Profile D: Shared Contracts & Core Libraries

Profile D governs shared API schemas, client SDKs, common domain utilities, and serialization protocols.

### 1. Architectural Model: Contract-First & Multi-Language Generation
All contracts originate from machine-readable specifications and generate typed code for Profiles A, B, and C:

```text
┌─────────────────────────────────────────────────────────────┐
│  Schema Authority (OpenAPI 3.1 YAML / Protobuf v3 / JSON-S) │
│  Single source of truth for all cross-service communication │
├─────────────────────────────────────────────────────────────┤
│  Automated Multi-Target Codegen Targets in Nx               │
│  - generate-ts: TypeScript DTOs & Zod schemas for Profile B │
│  - generate-dart: Dart models & client for Profile C        │
│  - generate-go: Go structs & router interfaces for Profile A│
├─────────────────────────────────────────────────────────────┤
│  Mechanical Schema Breaking Gate                            │
│  Automated diffing (oasdiff / buf breaking) vs origin/main  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Canonical Directory Layout
```text
libs/<library-name>/
├── project.json
├── AGENT.md                          # Profile D manifest
├── schemas/
│   ├── openapi/                      # OpenAPI specification files
│   └── proto/                        # Protocol buffer definitions
├── src/
│   ├── generated/                    # Code generated via buf / openapi-generator
│   └── validators/                   # Contract conformance validators
└── tests/
    ├── compatibility/                # Backward compatibility & schema breaking tests
    └── unit/                         # Serialization & roundtrip validation tests
```

### 3. Non-Negotiable Mandates
- **Semantic Versioning (SemVer)**: Strictly enforce SemVer: MAJOR (breaking changes), MINOR (backwards-compatible additions), PATCH (fixes).
- **Automated Multi-Target Codegen**: Schemas must define Nx codegen targets:
  - `generate-ts`: Generates typed TypeScript contracts and runtime schemas.
  - `generate-dart`: Generates Dart classes and serialization models for Flutter clients.
  - `generate-go`: Generates Go struct definitions and interface handlers for backend services.
- **Mechanical Breaking Change Gate**: PR CI pipelines must run schema diffing (`oasdiff` or `buf breaking`) comparing the active branch with `origin/main`. Breaking changes without a major SemVer bump trigger an immediate merge block.
- **Zero Ambient Side-Effects**: Shared libraries must not read environment variables, open network connections, or write to disk upon module import.
- **Purity**: Pure functional transformations and deterministic validation only.

### 4. Forbidden Patterns in Profile D
- **Heavy Framework Dependencies**: Pulling heavy UI or transport frameworks into contract packages. Must remain pure and lightweight.

---

## Universal Structural Boundaries & Anti-Sprawl Rules (All Profiles)

Regardless of whether a project belongs to Profile A, B, C, or D, all AI agents and engineers must observe these strict structural boundaries to prevent file sprawl, cognitive overload, and disorganized codebases:

### 1. File Size Ceilings & Split Heuristics
- **Soft Target**: $\le 300\text{--}400$ lines of code per file.
- **Hard Ceiling**: $800$ lines of code per file (excluding machine-generated code, lockfiles, and test snapshots).
- **Split Mandate**: When a file crosses 400 lines, evaluate separating secondary concerns (e.g., extracting validation schemas, subordinate helper classes, or state machine events). Crossing 800 lines without an accepted ADR is a **blocking defect**.

### 2. Micro-File Fragmentation & Merge Heuristics
- **The Fragmentation Anti-Pattern**: Agents frequently create excessive 5-to-15 line files (e.g. creating separate files for every trivial value object, single-line DTO, or one-liner domain exception). This leads to directory sprawl and navigation friction.
- **Co-Location Mandate**:
  - Small, tightly coupled domain value objects belonging to the same aggregate root must be co-located in the aggregate file or a single cohesive `value_objects.*` file.
  - A command/query and its immediate handler/DTO pair should be co-located in the same use-case file unless reused across multiple boundaries.
  - Domain exceptions belonging to a single bounded context should be co-located in `exceptions.*`.

### 3. Directory Depth & Hierarchy Limits
- **Maximum Nesting Depth**: Directories must never exceed **6 levels of nesting** from the subproject root (e.g. `src/features/billing/data/repositories/postgres/impl/v1/sub/` is strictly rejected).
- **Flatter is Better**: Organize code by bounded business feature or cohesive architectural layer rather than deep procedural hierarchies.

### 4. Folder File-Count Bounding & Anti-Sprawl
- **Folder Density Target**: A healthy directory contains between **3 and 25 files**.
- **Sprawl Ceiling**: Any single folder containing $> 35$ files must be sub-grouped into logical sub-slices (e.g. splitting `components/` into `components/ui/`, `components/navigation/`, `components/feedback/`).
- **Single-Item Ghost Directories**: Creating a directory that contains only 1 subdirectory that contains only 1 file (e.g. `src/services/billing/impl/default/DefaultBilling.ts`) is an anti-pattern. Collapse unneeded intermediate single-child directories.

### 5. Known Directory Taxonomy (Zero Dumping Grounds)
All files must reside under declared, semantically meaningful directories matching their profile. The following generic dumping grounds are strictly forbidden:
- `utils/`, `helpers/`, `common/`, `misc/`, `shared/` (without domain qualification), `temp/`, `scratch/`.
- Utilities must be placed in a domain-qualified or capability-qualified module (e.g. `src/crypto/`, `src/telemetry/`, `src/formatting/`).

# Enterprise Value-Driven Testing Matrix

This specification establishes the testing standards for all `enterprise-product` projects. Shallow, happy-path-only testing is strictly prohibited. Tests must verify resilience, data integrity, and failure handling under realistic conditions.

---

## 1. Coverage & Verification Gates

| Scope / Component | Minimum Line Coverage | Minimum Branch Coverage | Execution Environment |
|---|---|---|---|
| **Pure Domain Layer** (Entities, Value Objects, Domain Services) | **$\ge 95\%$** | **$\ge 95\%$** | In-process, zero I/O, ultra-fast ($< 10\text{ms}$) |
| **Application Layer** (Use Cases, Command Handlers) | **$\ge 90\%$** | **$\ge 90\%$** | In-process with port fakes/in-memory aggregates |
| **Infrastructure Adapters** (Persistence, Messaging, Gateways) | **$\ge 80\%$** | **$\ge 80\%$** | **Real ephemeral containers** (Podman / Testcontainers) |
| **Web UI Components** (Profile B: Features & Forms) | **$\ge 85\%$** | **$\ge 80\%$** | Headless browser / jsdom with Axe-core a11y checks |
| **Mobile State Machines** (Profile C: BLoC / Repositories) | **$\ge 90\%$** | **$\ge 85\%$** | Dart unit & widget test runner |
| **Shared Contracts & SDKs** (Profile D) | **$\ge 95\%$** | **$\ge 95\%$** | Roundtrip schema serialization & compatibility checks |

---

## 2. Mandatory Test Types

Every non-trivial feature must include a multi-layered test suite spanning these five mandatory categories:

```text
┌────────────────────────────────────────────────────────┐
│ 5. Concurrency & Race Condition Tests                  │
│    Parallel worker executions, optimistic lock checks  │
├────────────────────────────────────────────────────────┤
│ 4. Failure & Resilience Tests                          │
│    Timeouts, circuit breakers, retries, DLQ processing │
├────────────────────────────────────────────────────────┤
│ 3. Contract & Compatibility Tests                      │
│    OpenAPI schema validation, Protobuf wire checks     │
├────────────────────────────────────────────────────────┤
│ 2. Integration Tests (Ephemeral Real Containers)       │
│    PostgreSQL, Redis, Kafka running via Podman         │
├────────────────────────────────────────────────────────┤
│ 1. Domain & Unit Tests (Pure Logic)                    │
│    Invariants, business rules, edge cases, zero I/O    │
└────────────────────────────────────────────────────────┘
```

### 2.1 Domain & Unit Tests
- Execute in pure memory with zero network, filesystem, or database I/O.
- Must test: Boundary conditions, integer overflow/underflow, empty and malformed inputs, valid and invalid business state transitions.
- Must verify that domain events are emitted with correct payloads.

### 2.2 Integration Tests (Ephemeral Real Containers)
- **The In-Memory SQL Emulator Ban**: Replacing PostgreSQL or MySQL with in-memory SQLite or H2 in integration tests is strictly prohibited. Subtle differences in indexing, JSON operators, concurrency isolation, and dialect syntax create silent production bugs.
- **Execution**: Use Testcontainers (e.g., `testcontainers-go`, `testcontainers-node`, `testcontainers-dotnet`, `testcontainers-python`) or Lerd Podman quadlet containers.
- Verify: Full schema migrations, raw SQL queries, transaction rollbacks on failure, unique constraint violations, and connection pool behavior.

### 2.3 Contract & Compatibility Tests
- Validate that API responses match OpenAPI 3.1 / Protobuf schemas exactly.
- Verify backward compatibility: Old client payloads must be parseable by new server versions without breaking deserialization.

### 2.4 Failure & Resilience Tests
- Test what happens when downstream systems fail.
- Simulate:
  - Network timeouts (verify that the client aborts cleanly within configured timeout).
  - Upstream 500 errors (verify exponential backoff with jitter and retry caps).
  - Sustained outages (verify circuit breaker trips and fallback response is served).
  - Unprocessable messages (verify routing to Dead Letter Queue without crashing the consumer).

### 2.5 Concurrency & Race Condition Tests
- Execute concurrent updates against the same aggregate root from multiple threads or goroutines.
- Verify that optimistic locking throws a concurrency conflict or that row-level locking serializes writes safely without data corruption or deadlocks.

---

## 3. UI State-Machine Testing (Profiles B & C)

UI tests must never verify only the happy rendering state. Every dynamic UI component must have tests covering all four fundamental states:

1. **Loading State**: Displays skeleton / spinner; interactive elements are disabled.
2. **Empty State**: Displays clear call-to-action when data collection is empty; no broken layout or unhandled null errors.
3. **Success State**: Displays formatted domain data; accessibility tree is fully navigable.
4. **Error State**: Displays actionable error notification when API fails; provides a retry button that can recover cleanly.

---

## 4. Prohibition of Mock-Only Verification

- **Mocking Banned for Internal Business Logic**: Mocking domain entities or pure use cases to test other domain entities is forbidden. Test pure logic using real instances.
- **Mocking at Boundaries**: Mocking is permitted only at the absolute edge of the system for external third-party services that cannot be containerized locally (e.g., Stripe, SendGrid, Twilio).
- **Clock Virtualization**: Do not sleep in tests or mock system time ambiently. Inject a `ClockPort` (or `Clock` interface) and advance virtual time deterministically.

---

## 5. Mutation Testing Protocol

For critical business logic (billing, authorization, financial calculations, state transitions):
- Run mutation testing (e.g., Stryker for TS/C#, Mutmut for Python, Pitest for Java/Kotlin).
- Mutation Score Requirement: Critical domain logic must maintain a **Mutation Score $\ge 85\%$**. If a mutant (e.g., `>` changed to `>=`, or a condition inverted) survives without breaking a test, the test suite is inadequate and must be enhanced.

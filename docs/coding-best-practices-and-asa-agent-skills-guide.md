# Coding Best Practices Skills Catalog & Aea Toolset Guide

A reference guide documenting top open-source coding best practice skill repositories and defining the core language-specific coding standards to equip **Aea** (Genesis), our primary implementation coding agent orchestrated by **Asa**.

---

## 1. Architectural Context: Asa vs. Aea

In our multi-agent architecture:
* **Asa (`src/asa/`)**: The multi-agent orchestrator and execution harness. Asa handles session routing, worktree isolation, batch coordination, context envelopes, and verification gates.
* **Aea (`src/asa/agents/aea.md`)**: The primary coding subagent (called *Genesis*). Aea receives failing tests and context payloads, then writes the minimal, robust implementation to turn tests green without modifying the test suite.

This guide details the external skill collections available for research, along with the concrete language coding practices to configure into **Aea's toolset**.

---

## 2. Top Repositories & Skill Collections

### A. Modular Role & Quality Suites

1. **[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)**
   * **Scope:** 380+ modular skills across development, testing, and devops.
   * **Key Modules:**
     * `standards/quality/`: Automated testing, linting gates, and code-smell prevention.
     * `standards/security/`: OWASP vulnerability checks and secret protection.
     * `standards/git/`: Atomic commits, branch discipline, and clear PR summaries.
     * `engineering/zero-hallucination-coder`: Pre-execution validation steps.
     * `engineering/strict-api`: Defensive API contracts and schema validation.

2. **[Jeffallan/claude-skills](https://github.com/Jeffallan/claude-skills)**
   * **Scope:** 67 specialized engineering personas and 370+ reference guides.
   * **Key Modules:**
     * `fullstack-guardian`: Architectural boundary defense and clean separation of concerns.
     * `secure-code-guardian`: Input sanitization, memory safety, and auth validation.
     * `test-master`: Integration testing, unit testing hierarchies, and mock isolation.
     * `typescript-pro`, `python-pro`, `go-expert`, `swift-expert`: Language-specific idiomatic conventions.
     * `debugging-wizard`: Systematic root-cause isolation.

---

### B. Deep Principles & Architecture Invariants

3. **[cursor/plugins (pstack/skills)](https://github.com/cursor/plugins/tree/main/pstack/skills)**
   * **Scope:** 20 standalone engineering principles and verification skills.
   * **Key Modules:**
     * `principle-type-system-discipline`: Make illegal states unrepresentable; strict boundary parsing.
     * `principle-boundary-discipline`: Decouple pure domain logic from side-effecting I/O.
     * `principle-encode-lessons-in-structure`: Prevent bugs mechanically via tests, types, and lints.
     * `principle-sequence-verifiable-units`: Break complex refactors into atomic, green-verified steps.
     * `principle-subtract-before-you-add`: Delete dead code and simplify baselines before adding features.
     * `typescript-best-practices` & `tdd`: Concrete typing rules and red-green-refactor loops.

4. **[mattpocock/skills](https://github.com/mattpocock/skills)**
   * **Scope:** Deep TypeScript, API design, and module architecture.
   * **Key Modules:**
     * `codebase-design`: Interface deepening, module seams, and high information-hiding.
     * `setup-ts-deep-modules`: `dependency-cruiser` configs enforcing entry-point boundaries.
     * `domain-modeling`: Rich entity modeling and ADR recording.
     * `diagnosing-bugs`: Systematic hypothesis testing and reproduction scripts.

---

### C. Framework & Language Rule Hubs

5. **[PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)**
   * **Scope:** 500+ community-curated rulesets for frameworks and languages (Next.js, React, FastAPI, Go, Rust, Swift, Tailwind, Clean Architecture).

6. **[anthropics/skills](https://github.com/anthropics/skills)**
   * **Scope:** Anthropic's official reference repository for Agent Skills standard (`SKILL.md`).

---

## 3. Core Behavioral Invariants for Aea

When Aea writes code to satisfy failing tests, five behavioral invariants must guide every implementation:

1. **Parse at Boundaries, Never Validate Ad-Hoc:** Data entering from outside (HTTP requests, files, environment variables, CLI arguments) must be parsed into strongly typed domain objects at the edge. Internal code must never handle raw, unvalidated primitives.
2. **Make Illegal States Unrepresentable:** Structure types, enums, and models so invalid business states cannot compile or instantiate.
3. **Decouple Pure Logic from Side Effects:** Keep business calculations, data transformations, and domain rules isolated from I/O, database queries, network requests, and the system clock.
4. **Sequence Verifiable Units:** Implement solutions in small increments. Each unit must end in an observable, verifiable green state (tests passing, linter clean) before proceeding to the next.
5. **Fix Root Causes, Never Patch Symptoms:** Trace defects to their originating structural flaw. Do not wrap broken assumptions in defensive null checks.

---

## 4. Language-Specific Coding Practices for Aea

This section defines the concrete language standards to equip Aea when implementing solutions across Aki's core development stack:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       AEA LANGUAGE STANDARDS MATRIX                     │
├───────────────────┬─────────────────────────────────────────────────────┤
│ TypeScript / JS   │ Strict mode, Zod boundary parsing, branded types   │
│ Python            │ Type hints, Pydantic v2, pytest suites, contextmgrs │
│ Swift / iOS       │ Value semantics, Swift Concurrency, SwiftUI state   │
│ Go                │ Explicit error checks, context, table-driven tests  │
│ Java              │ Records/immutability, strong typing, clean packages │
│ SQL               │ Parameterized queries, explicit indices, migrations │
└───────────────────┴─────────────────────────────────────────────────────┘
```

---

### 1. TypeScript & JavaScript Standards

* **Strict Typing Invariants:**
  * `strict: true` and `noImplicitAny: true` must be enabled.
  * Ban the use of `any`. Use `unknown` and narrow with type guards or schemas.
  * Avoid type assertions (`as Type`) except at verified external seams.
* **Domain Modeling & Primitives:**
  * Use branded types for nominal IDs (e.g. `type UserId = string & { readonly __brand: unique symbol }`).
  * Prefer discriminated unions over optional properties with boolean flags.
* **Boundary Validation:**
  * Use Zod or Valibot at all API, disk, and IPC boundaries. Parse once into typed records.
* **Function & State Design:**
  * Explicit return types on all exported functions.
  * Treat objects and arrays as immutable (`readonly`, `ReadonlyArray`). Use pure transformations (`map`, `filter`, `reduce`) over in-place mutations.

---

### 2. Python Standards

* **Static Typing & Signatures:**
  * All functions and class methods must carry complete type annotations (`typing`, `Union`, `Optional`, `Callable`).
  * Enforce strict static analysis with `mypy` or `pyright`.
* **Data Structures & Models:**
  * Use `dataclasses(frozen=True)` for internal value objects and `pydantic.BaseModel` for external serialization/deserialization.
* **Resource & Error Management:**
  * Always use context managers (`with` statements) for file handles, sockets, database sessions, and locks.
  * Define explicit domain exception hierarchies inheriting from a project base exception. Never catch bare `Exception` without re-raising or logging context.
* **Testing & Quality:**
  * Test suites using `pytest`. Use fixtures for setup and parametrize tests for table-driven test cases.

---

### 3. Swift & iOS Standards

* **Value Types & Immutability:**
  * Prefer `struct` and `enum` over `class`. Use classes only when reference semantics or identity lifecycle is required.
  * Declare properties with `let` by default. Mark structs as `Sendable` when crossing concurrency domains.
* **Modern Concurrency:**
  * Use Swift Concurrency (`async`/`await`, `Task`, `TaskGroup`, `actor`) instead of raw GCD queues or completion handler callbacks.
  * Use `actor` for mutable shared state to prevent data races.
* **UI Architecture:**
  * In SwiftUI, strictly separate presentation views from business state (`@Observable`, `@StateObject`, ViewModels).
  * Keep views modular and lightweight to maximize view recomputation performance.
* **Error Handling:**
  * Use typed errors (`enum AppError: Error`) and `throws`. Avoid force unwrapping (`!`) and force try (`try!`).

---

### 4. Go Standards

* **Error Handling:**
  * Handle errors immediately where they occur (`if err != nil`). Wrap errors with context using `fmt.Errorf("action description: %w", err)`.
* **Concurrency & Context:**
  * Pass `context.Context` as the first parameter to any I/O, database, or long-running function.
  * Ensure all goroutines have a guaranteed exit condition triggered by context cancellation to prevent goroutine leaks.
* **Struct Design & Packages:**
  * Keep packages small, focused, and single-purpose. Avoid monolithic `utils` packages.
  * Accept interfaces, return concrete structs.
* **Testing:**
  * Use table-driven test suites using `t.Run` subtests.

---

### 5. Java Standards

* **Modern Language Features:**
  * Use `record` for immutable data carriers and DTOs.
  * Use `var` only when the type is obvious from the right-hand side.
* **Immutability & Safety:**
  * Prefer immutable collections (`List.of()`, `Set.of()`, `Map.of()`).
  * Return `Optional<T>` for methods that may produce no result; never return bare `null`.
* **Architecture:**
  * Maintain clean package layering (Domain, Service, Repository, Controller).
  * Avoid deep inheritance hierarchies; prefer composition over inheritance.

---

### 6. SQL & Database Standards

* **Query Safety:**
  * All dynamic SQL queries must use parameterized placeholders. String interpolation into SQL queries is strictly banned.
* **Schema & Indexing:**
  * Every table must have a primary key.
  * Foreign key columns and columns used in `WHERE`, `JOIN`, or `ORDER BY` clauses must be indexed.
* **Transactions:**
  * Wrap multi-table write operations in explicit transactions (`BEGIN ... COMMIT`) with rollback on failure.

---

## 5. Integration Architecture for Aea

To equip Aea with these language capabilities without bloating its system prompt:

1. **Context Envelope Injection:** Asa's orchestrator inspects the target codebase or file extensions during task framing and injects the corresponding language standard into Aea's `--context-file` envelope under `global_constraints`.
2. **Modular Reference Files:** Store language standards as reference files under `skills/coding/references/` (e.g. `typescript.md`, `python.md`, `swift.md`, `go.md`) so Aea loads them on demand via progressive disclosure.
3. **Verification Gates:** Asa executes language-specific linters and test runners (`pytest`, `tsc --noEmit`, `swift test`, `go test`) in the pre/post worktree verification gate to automatically validate Aea's output.

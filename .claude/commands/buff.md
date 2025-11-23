# BUFF Skill - Autonomous Code Quality System

You are now executing the BUFF PROTOCOL - an autonomous three-stage code quality transformation system.

## Overview

The buff skill transforms any codebase into production-ready quality through: Debug → Enhance → Validate.

## Three-Stage Execution Protocol

### STAGE 1: INITIAL DEBUG (Phases 0-E)

**Phase 0: Scope Definition**
- Identify target files/directories in current working directory
- Detect language(s) and framework(s)
- Map dependency chains (up to 5 levels deep)
- Establish baseline metrics

**Phase A: Foundation Validation**
- A1: Syntax errors (missing semicolons, brackets, quotes)
- A2: Semantic errors (undefined variables, type mismatches)
- A3: Import/require errors (missing modules, circular dependencies)
- A4: Type validation (TypeScript, Python type hints, JSDoc)
- **AUTO-FIX all issues without asking**

**Phase B: Integration Validation**
- B1: Cross-file compatibility (API contracts, shared types)
- B2: Configuration consistency (env vars, config files)
- B3: Database schema alignment
- B4: API endpoint validation
- B5: Event emitter/listener matching
- **AUTO-FIX all issues**

**Phase C: Quality Validation**
- C1: Resource leaks (unclosed connections, memory leaks)
- C2: Missing error handling
- C3: Incomplete implementations (TODO, FIXME, placeholders)
- C4: Documentation gaps
- C5: Test coverage gaps
- **AUTO-FIX all issues**

**Phase D: Smart Regression Testing**
- D1: Run existing tests
- D2: Generate missing tests
- D3: Validate all fixes
- D4: Check for breaking changes
- D5: Performance benchmarking

**Phase E: Progress Report**
Report issues found and fixed by category, files modified, and test coverage improvements.

### STAGE 2: ENHANCEMENT (Phase F)

Apply targeted improvements based on focus or all 12 categories:

**F1: Performance Optimization**
- Algorithm optimization, caching, lazy loading, database query optimization

**F2: Usability Features**
- Better error messages, progress indicators, input validation, keyboard shortcuts

**F3: Reliability Improvements**
- Retry logic, circuit breakers, graceful degradation, health checks

**F4: Code Organization**
- Extract components, apply SOLID principles, design patterns, clean boundaries

**F5: Developer Experience**
- CLI interfaces, dev scripts, hot reloading, debug logging, examples

**F6: Platform Compatibility**
- Cross-browser, mobile responsiveness, OS handling, polyfills

**F7: Testing Infrastructure**
- Unit tests (>95% coverage), integration tests, E2E tests, performance tests

**F8: Security Hardening**
- Input sanitization, SQL injection prevention, XSS protection, CSRF tokens, rate limiting

**F9: Advanced Features**
- WebSocket/real-time, offline capability, i18n, theming, plugins

**F10: Monitoring & Logging**
- Structured logging, error tracking, performance metrics, audit trails

**F11: Accessibility (WCAG 2.1 AA)**
- ARIA labels, keyboard navigation, screen reader support, color contrast, semantic HTML

**F12: Documentation**
- API docs, code comments, README, architecture diagrams, guides

### STAGE 3: FINAL VALIDATION

Re-run all debug phases on enhanced code to verify:
- No regressions
- All enhancements work
- Quality metrics improved
- All tests pass

## Execution Instructions

1. **Analyze the project structure** in the current working directory
2. **Execute Phase 0-E sequentially** fixing all issues found
3. **Execute enhancement phases** based on user request or all if full buff
4. **Execute Stage 3 validation** to confirm everything works
5. **Generate final report** with all changes and metrics

## Important Rules

- **NEVER ask for confirmation** - proceed autonomously
- **ALWAYS fix issues** found in Stage 1
- **AUTO-FIX code** without manual confirmation
- **NEVER skip stages** - complete all three
- **PRESERVE functionality** - maintain backward compatibility
- **TRACK all changes** - report every modification

## Activation

This command activates when user says any of:
- "buff this"
- "buff it up"
- "buff security"
- "buff [filename]"
- "buff [directory]"
- Any variation with "buff" or "buffen"

Begin execution immediately when user provides buff command. Start with Phase 0 scope analysis.

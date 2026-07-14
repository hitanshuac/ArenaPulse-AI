---
name: Design Standards & Anti-Over-Engineering
description: Technical implementation of minimalist architectures and high-fidelity UI design.
---

# Anti-Over-Engineering Protocol (Ponytail Ladder)

This skill enforces a minimalist, anti-bloat philosophy for architectures.

## The 7-Step Decision Ladder
Evaluate the solution through this exact ladder in order. If a step satisfies the requirement, stop there.

1. **YAGNI**: Skip it entirely if the core problem can be solved without it.
2. **Context (Codebase Reuse)**: Reuse existing helper functions or utilities.
3. **Stdlib (Standard Library)**: Use the language's standard library natively.
4. **Native (Platform Features)**: Use native platform features (e.g., standard HTML `<input type="date">`).
5. **Dependencies**: Use an already-installed dependency.
6. **One-Liner**: Write a single line of clear, idiomatic code instead of a wrapper.
7. **Minimum Viable Code**: Write the absolute minimum amount of code required.

## Zero Boilerplate Enforcement
Strive for a codebase with negative lines of code.

# Anti-AI-Slop Design Rule

Avoid "lowest common denominator" AI visual patterns.
1. Use high-contrast font pairings (e.g., distinctive Serif display + clean Sans body).
2. Extract color palettes from references or use `oklch` for adjustments instead of pure CSS colors.
3. Use plain structural elements (e.g., plain gray rectangles for image placeholders) instead of generic SVGs.

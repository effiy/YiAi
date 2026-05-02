---
paths:
  - "docs/*/04_usage-document.md"
---

# Usage Document Specification

> For end users, operation scenarios first, FAQs second. Upstream: 03/02/01.

## Document Structure

### 1. Header

Standard header + navigation anchors (Feature Intro | Quick Start | Operation Scenarios | FAQ | Tips).

### 2. Feature Introduction

100-200 words + 3 core features (🎯⚡🔧) + target audience

### 3. Quick Start

Prerequisites (checklist) + 30-second onboarding (3-5 steps)

### 4. Operation Scenarios (Core)

6-8 scenarios total, split into two groups:

**Recommended Scenarios (正面场景)** — 3-5 items:
- Cover the user's primary success paths and high-frequency operations.
- Each item: applicable situation → operation steps → expected results → notes (✅).

**Anti-patterns / Cautionary Scenarios (反面场景)** — 2-3 items:
- Cover common misoperations, prohibited actions, and easily confused flows.
- Each item: wrong operation / misconception → consequence / risk → correct approach → notes (❌).

Both groups must correspond to real features described in upstream documents (02/03); fabrication is prohibited.

### 5. FAQ

5-10 items: 💡 basics / ⚙️ advanced / 🔧 troubleshooting

### 6. Tips and Hints

💡 practical tips (3-5) / ⌨️ shortcuts (if applicable) / 📚 best practices (2-3)

### 7. Appendix (Optional)

Glossary / command cheat sheet / related resources

## Writing Principles

User perspective / scenario-driven / clear steps / problem-oriented

## Save Location

`docs/<feature-name>/04_usage-document.md`

## Quality Check

> See [checklists/usage-document.md](../checklists/usage-document.md)

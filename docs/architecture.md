# Architecture

```mermaid
flowchart LR
Planner --> Researcher
Researcher --> Reviewer
Reviewer -->|more evidence; bounded| Researcher
Reviewer --> Writer
```

See the source modules and tests for implementation details. External model/API availability is independent of offline test success.

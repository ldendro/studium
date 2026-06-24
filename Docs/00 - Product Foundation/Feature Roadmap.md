## Project name: Studium  
  
## Roadmap Philosophy  
  
Studium will be built phase by phase.  
  
Each phase focuses on one major feature area and includes both planning and implementation. Within each phase, development should be split into careful implementation branches, but the detailed branch plan should live in that phase’s dedicated implementation plan.  
  
The roadmap is designed so each phase lays the foundation for the next. Later phases may refine or extend earlier features when the system requires stronger behavior.  
  
The first priority is not to build a polished interface immediately. The first priority is to build the foundation that allows Studium to understand, organize, and safely write to a knowledge vault.  
  
---
The phases will proceed as follows:
1. Phase 1: Vault Storage Core
2. Phase 2: Concept Graph Core
3. Phase 3: Create
4. Phase 4: Source Content Intelligence
5. Phase 5: Agent Review
6. Phase 6: Backlog
7. Phase 7: Retention
8. Phase 8: Mastery Dashboard
9. Phase 9: Personal Learning Model
10. Phase 10: Productization & Multi-User Platform*
*Future phases will be implemented according to ideas developed throughout the initial 8 phases*
*Optional Phase, only relevant if Studium proves useful enough as a personal system to become a product for others
## Core Dependency Chain

Vault Storage Core
↓
Concept Graph Core
↓
Create
↓
Source Content Intelligence
↓
Agent Review
↓
Backlog
↓
Retention
↓
Mastery Dashboard
↓
Personal Learning Model
↓
Productization

## Important Notes
- Create is the first major user-facing workflow, but it should not be built before the vault and concept intelligence foundations.
- Existing notes should be upgraded through the Create upload/import workflow rather than bulk-migrated automatically.
- The system should start with a test vault before writing to the real Obsidian vault.
- Studium should use Markdown as the durable knowledge format.
- SQLite is acceptable for structured data such as backlog items.
- The LLM layer should be provider-agnostic, with local-first usage as a technical preference.
- Hybrid keyword + embedding search should support concept matching.
- Each phase should have its own implementation plan with branch-level detail.
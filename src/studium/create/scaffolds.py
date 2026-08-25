"""Active-learning scaffold selection and Markdown generation."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from studium.create.models import ModuleProposal
from studium.schemas import ConceptType, ScaffoldModuleOrigin, ScaffoldModuleType
from studium.serialization.concept_id import slugify_title


def recommend_modules(
    concept_type: ConceptType,
    *,
    intent: str,
    requested: ScaffoldModuleType | None = None,
    preferences: Iterable[ScaffoldModuleType] = (),
) -> list[ModuleProposal]:
    lower = intent.casefold()
    types: list[ScaffoldModuleType] = [ScaffoldModuleType.CONCEPTUAL_EXPLANATION]
    if concept_type in {
        ConceptType.MATHEMATICAL_CONCEPT,
        ConceptType.ALGORITHM,
        ConceptType.THEORY_CONCEPT,
    }:
        types.append(ScaffoldModuleType.WORKED_EXAMPLE)
    if concept_type in {
        ConceptType.ALGORITHM,
        ConceptType.PROGRAMMING_CONCEPT,
        ConceptType.SYSTEM_DESIGN_CONCEPT,
        ConceptType.TOOLING_CONCEPT,
    }:
        types.append(ScaffoldModuleType.CODE_IMPLEMENTATION)
    if any(word in lower for word in ("derive", "proof", "equation", "gradient", "calculus")):
        types.append(ScaffoldModuleType.DERIVATION)
    if any(word in lower for word in ("compare", "difference", "versus", " vs ")):
        types.append(ScaffoldModuleType.COMPARISON)
    if any(word in lower for word in ("implement", "code", "python", "build")):
        types.append(ScaffoldModuleType.CODE_IMPLEMENTATION)
    if any(word in lower for word in ("example", "calculate", "manual", "solve")):
        types.append(ScaffoldModuleType.WORKED_EXAMPLE)
    if requested is not None:
        types.append(requested)
    types.extend(preferences)
    types.append(ScaffoldModuleType.APPLICATION)

    unique: list[ScaffoldModuleType] = []
    for module_type in types:
        if module_type not in unique:
            unique.append(module_type)
    return [
        module_proposal(
            module_type,
            selected=index < 4,
            reason=_module_reason(module_type, concept_type, requested=requested),
        )
        for index, module_type in enumerate(unique)
    ]


def module_proposal(
    module_type: ScaffoldModuleType,
    *,
    title: str | None = None,
    focus: str | None = None,
    selected: bool = True,
    reason: str = "Supports active reconstruction.",
    origin: ScaffoldModuleOrigin = ScaffoldModuleOrigin.AGENT_RECOMMENDED,
) -> ModuleProposal:
    display = title or _default_title(module_type)
    token = uuid4().hex[:8]
    return ModuleProposal(
        id=f"module_{slugify_title(display)}_{token}",
        type=module_type,
        title=display,
        focus=focus,
        selected=selected,
        reason=reason,
        origin=origin,
    )


def render_new_concept_body(title: str, modules: list[ModuleProposal]) -> str:
    selected = [module for module in modules if module.selected]
    index_lines = "\n".join(
        f"- [{' ' if module.selected else 'x'}] [[#{module.title}|{module.title}]] "
        f"— `{module.type.value}`"
        for module in selected
    )
    module_markdown = "\n\n".join(render_module(module) for module in selected)
    return f"""# {title}

## Concept Overview

Reconstruct the concept in your own words before consulting a source.

- **Problem this concept solves:** _Write one sentence._
- **Core mechanism:** _Explain what changes and why._
- **When it is useful:** _Name a concrete situation._
- **Boundary:** _What is easily confused with this concept?_

## Prerequisites

- [ ] Identify the minimum concepts you need to explain this without circular reasoning.
- [ ] Link each accepted prerequisite and state why it is required.

## Module Index

{index_lines or "_No scaffold modules selected._"}

## Scaffold Modules

{module_markdown or "_Add a scaffold module when you know what kind of practice is needed._"}

## Related Concepts

- Add relationships only after checking their direction and learning role.

## Open Questions / Gaps

- [ ] What still feels hand-wavy?
- [ ] What would falsify or limit this explanation?
"""


def render_module(module: ModuleProposal) -> str:
    heading = f"### {module.title}"
    focus = f"\n\n> Focus: {module.focus}" if module.focus else ""
    template = _TEMPLATES[module.type]
    return f"{heading}{focus}\n\n{template}".strip()


def insert_modules(body: str, modules: list[ModuleProposal]) -> str:
    selected = [module for module in modules if module.selected]
    if not selected:
        return body
    rendered = "\n\n".join(render_module(module) for module in selected)
    marker = "## Related Concepts"
    if marker in body:
        before, after = body.split(marker, 1)
        prefix = before.rstrip()
        if "## Scaffold Modules" not in prefix:
            prefix += "\n\n## Scaffold Modules"
        return f"{prefix}\n\n{rendered}\n\n{marker}{after}"
    return f"{body.rstrip()}\n\n## Scaffold Modules\n\n{rendered}\n"


def update_module_index(body: str, modules: list[ModuleProposal]) -> str:
    selected = [module for module in modules if module.selected]
    if not selected:
        return body
    lines = "\n".join(
        f"- [ ] [[#{module.title}|{module.title}]] — `{module.type.value}`" for module in selected
    )
    heading = "## Module Index"
    next_heading = "## Scaffold Modules"
    if heading not in body:
        return body
    before, remainder = body.split(heading, 1)
    if next_heading in remainder:
        _old, after = remainder.split(next_heading, 1)
        return f"{before}{heading}\n\n{lines}\n\n{next_heading}{after}"
    return f"{before}{heading}\n\n{lines}\n\n{remainder.lstrip()}"


def _default_title(module_type: ScaffoldModuleType) -> str:
    names = {
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION: "Conceptual Reconstruction",
        ScaffoldModuleType.WORKED_EXAMPLE: "Worked Example",
        ScaffoldModuleType.CODE_IMPLEMENTATION: "Implementation From Memory",
        ScaffoldModuleType.IMPLEMENTATION_NOTES: "Implementation Notes",
        ScaffoldModuleType.COMPARISON: "Comparison",
        ScaffoldModuleType.DERIVATION: "Derivation",
        ScaffoldModuleType.APPLICATION: "Application",
        ScaffoldModuleType.MISCONCEPTION_DEBUGGING: "Misconception Debugging",
        ScaffoldModuleType.CUSTOM: "Custom Practice",
    }
    return names[module_type]


def _module_reason(
    module_type: ScaffoldModuleType,
    concept_type: ConceptType,
    *,
    requested: ScaffoldModuleType | None,
) -> str:
    if module_type == requested:
        return "Directly requested in this learning intent."
    reasons = {
        ScaffoldModuleType.CONCEPTUAL_EXPLANATION: "Builds a mechanism-first explanation.",
        ScaffoldModuleType.WORKED_EXAMPLE: (
            "Turns abstract understanding into a checkable procedure."
        ),
        ScaffoldModuleType.CODE_IMPLEMENTATION: "Tests whether the mechanism can be reconstructed.",
        ScaffoldModuleType.IMPLEMENTATION_NOTES: "Captures constraints and practical trade-offs.",
        ScaffoldModuleType.COMPARISON: "Sharpens the boundary between nearby concepts.",
        ScaffoldModuleType.DERIVATION: "Makes mathematical dependencies explicit.",
        ScaffoldModuleType.APPLICATION: "Connects understanding to a concrete decision.",
        ScaffoldModuleType.MISCONCEPTION_DEBUGGING: "Surfaces likely failure modes.",
        ScaffoldModuleType.CUSTOM: "Supports the requested learning shape.",
    }
    return f"{reasons[module_type]} Recommended for {concept_type.value.replace('_', ' ')}."


_TEMPLATES: dict[ScaffoldModuleType, str] = {
    ScaffoldModuleType.CONCEPTUAL_EXPLANATION: """#### Reconstruct

Without looking at a source, explain:

1. What problem requires this concept?
2. What mechanism produces the result?
3. Which assumptions make the explanation valid?

#### Check your model

- **Key terms:** _Define each in plain language._
- **Minimal example:** _Use the smallest example that still demonstrates the mechanism._
- **Common confusion:** _State the tempting but incorrect explanation._""",
    ScaffoldModuleType.WORKED_EXAMPLE: """#### Given

Write a concrete setup with values, units, or state.

#### Solve before revealing

1. _Write the first transformation and justify it._
2. _Compute the intermediate result._
3. _Check sign, shape, units, or invariant._
4. _Explain the result in words._

#### Error reflection

- Where could a plausible wrong answer arise?
- Which check catches it earliest?""",
    ScaffoldModuleType.CODE_IMPLEMENTATION: """#### Contract

- **Input:** _Types, shapes, and constraints._
- **Output:** _What must be returned or changed?_
- **Invariant:** _What must remain true?_

#### Pseudocode from memory

```text
TODO
```

#### Implementation

```python
def implement():
    raise NotImplementedError
```

#### Tests

- [ ] Small deterministic case
- [ ] Boundary / failure case
- [ ] Comparison against a trusted result""",
    ScaffoldModuleType.IMPLEMENTATION_NOTES: """#### Design choices

| Choice | Why | Trade-off |
| --- | --- | --- |
| _Fill_ | _Fill_ | _Fill_ |

#### Failure modes

- _What breaks first?_
- _What signal would reveal it?_

#### Operational checklist

- [ ] Correctness
- [ ] Performance
- [ ] Observability""",
    ScaffoldModuleType.COMPARISON: """#### Comparison target

Compare this concept with: _Name the closest alternative._

| Dimension | This concept | Alternative |
| --- | --- | --- |
| Mechanism | _Fill_ | _Fill_ |
| Assumptions | _Fill_ | _Fill_ |
| Strength | _Fill_ | _Fill_ |
| Failure mode | _Fill_ | _Fill_ |

#### Decision rule

Choose this concept when: _Write a concrete rule._""",
    ScaffoldModuleType.DERIVATION: """#### Starting assumptions

List every symbol and assumption before manipulating equations.

#### Reconstruct

$$
\\text{Start: } \\quad \\ldots
$$

1. _Apply one justified transformation._
2. _Name the rule used._
3. _Check dimensions or limiting behavior._

$$
\\text{Result: } \\quad \\ldots
$$

#### Interpret

Explain what each term in the final expression controls.""",
    ScaffoldModuleType.APPLICATION: """#### Scenario

Describe one situation where this concept changes a decision.

#### Apply

- **Goal:** _What outcome matters?_
- **Signal:** _What would you observe?_
- **Decision:** _How does the concept guide action?_
- **Limitation:** _When would this application fail?_

#### Transfer

Name a different domain where the same mechanism may apply.""",
    ScaffoldModuleType.MISCONCEPTION_DEBUGGING: """#### Predict the mistake

Write the most plausible incorrect explanation or solution.

#### Diagnose

- Which assumption is wrong?
- What counterexample exposes it?
- Which prerequisite would prevent the mistake?

#### Correct

Rewrite the explanation in one precise paragraph.""",
    ScaffoldModuleType.CUSTOM: """#### Learning objective

_State what successful reconstruction looks like._

#### Attempt

_Complete the task without consulting the answer._

#### Verification

_Record the evidence that the attempt is correct._""",
}

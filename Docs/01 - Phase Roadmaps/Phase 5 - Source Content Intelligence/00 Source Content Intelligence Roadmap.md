## Purpose

Build the source-aware intelligence layer of Studium.

Phase 5 allows Studium to process attached source material, retrieve relevant chunks, compare source content against an existing concept note or scaffold request, and generate source-grounded scaffold/module proposals with citations back to the source.

This phase answers:

> How does Studium use source material to make scaffolds more accurate, grounded, and useful for learning?

Phase 5 should not simply summarize a source.

It should use source material in relation to:

- a concept
    
- a learning request
    
- a scaffold module plan
    
- an existing concept note
    
- a new learning encounter
    
- a Search-to-Create handoff
    

The goal is not to analyze an entire textbook or source for its own sake. The goal is to retrieve and use the parts of the source that are relevant to the concept being learned.

---

## Why This Phase Comes Here

Phase 5 comes after Create because Phase 4 establishes the core scaffold creation and editing workflow.

Phase 5 improves Create by making scaffolds source-aware.

Before this phase, Create can generate concept scaffolds using the concept name, user query, graph context, and source metadata.

After this phase, Create can also use actual source content.

Phase 5 depends on:

- Phase 1: Vault Storage Core
    
- Phase 2: Concept Graph Core
    
- Phase 3: Search
    
- Phase 4: Create
    

Phase 5 should route its proposals back through Create’s proposal/editor/save workflow.

It should not directly mutate concept notes.

---

## Core Principle

Source Intelligence should help the user learn from the source, not replace the learning process.

The agent should retrieve source material, cite it, and use it to generate better scaffolds, but the user should still fill out, revise, and internalize the note.

Source Intelligence should be:

```text
source-grounded
concept-scoped
citation-backed
latency-conscious
cost-conscious
proposal-based
```

It should not become:

```text
a full-source summarizer
a hallucinated textbook interpreter
an automatic note overwriter
a heavy research assistant that analyzes irrelevant sections
```

---

## Supported Source Types

Phase 5 v1 should support source formats that can provide usable text for retrieval.

Initial supported formats:

```text
Markdown
plain text
PDFs with extractable text
text-based slide PDFs
article PDFs
textbook PDFs with extractable text
lecture note PDFs
transcripts
web article text if easily extractable
```

Later formats:

```text
image-heavy PDFs
scanned PDFs
handwritten notes
audio/video transcription
slides with complex diagrams
Jupyter notebooks
code repositories
EPUB textbooks
OCR-heavy documents
```

Important PDF boundary:

> Phase 5 supports PDFs when useful text can be extracted. This includes many textbooks, lecture notes, exported articles, and text-based slide PDFs. It does not guarantee reliable OCR for scanned, handwritten, or image-only documents yet.

---

## PDF Viewer Requirement

PDF sources should be displayed through a PDF viewer that preserves the original layout.

The user-facing source pane should show the PDF as it would appear outside Studium.

This matters because textbooks, slides, and lecture PDFs often contain:

```text
diagrams
figures
tables
math notation
layout cues
visual explanations
```

The RAG backend may extract text, chunks, embeddings, and page metadata, but the user should still see the original PDF.

Recommended model:

```text
Backend:
extract text, chunks, embeddings, locations

Frontend:
render original PDF with page navigation and citation highlighting
```

For non-PDF text sources, the source pane should render the original Markdown, transcript, or text as faithfully as possible.

---

## Source Library

Phase 5 should introduce a basic Source Library.

A source should only need to be uploaded and processed once.

Example:

```text
Upload Hands-On Machine Learning once
↓
Studium stores source record, file reference, chunks, embeddings, and metadata
↓
Later Create sessions can choose the existing source
↓
Studium retrieves concept-relevant chunks from the already-processed source
```

This improves:

```text
storage efficiency
latency
cost
source reuse
metadata consistency
```

The Source Library should support:

```text
upload new source
choose existing source
search existing sources
view source processing status
view source metadata
reuse processed chunks and embeddings
```

---

## Existing Source Picker

Create should allow the user to choose an existing source from the Source Library.

The source picker should be searchable.

Searchable fields may include:

```text
source title
source type
author
tags
unit/chapter/lecture
file name
processed status
```

Example:

```text
Source: Hands-On Machine Learning
Unit: Chapter 4
Section: optional
```

The user should not have to re-upload the same textbook or lecture source for every concept.

---

## Source Processing Status

Source records and learning encounters should have separate statuses.

A source record status describes the processing state of the uploaded source itself.

Example:

```yaml
source_record:
  id: source_hands_on_ml_abc123
  title: Hands-On Machine Learning
  type: book_pdf
  file_path: /_studium_sources/hands_on_ml.pdf
  status: ready
```

Possible source record statuses:

```text
uploaded
text_extracted
chunked
embedded
ready
failed
```

A learning encounter status describes how that source contributed to a specific concept note.

Example:

```yaml
learning_encounters:
  - source:
      id: source_hands_on_ml_abc123
      title: Hands-On Machine Learning
      unit_type: chapter
      unit: Chapter 4
    role: primary
    contribution_status: source_analyzed
```

Possible learning encounter contribution statuses:

```text
pending
user_described
source_attached
source_analyzed
integrated
no_new_contribution_detected
```

This separation matters because one source may be fully processed, while its contribution to a specific concept may still be pending.

---

## Source Ingestion Pipeline

Phase 5 should use a hybrid ingestion strategy.

On upload:

```text
store source record
extract text if possible
chunk source text
preserve source locations
embed chunks
store processing metadata
mark source ready when complete
```

On use:

```text
retrieve chunks relevant to concept/query/module request
rerank candidate chunks
compare retrieved chunks against existing note or module plan
generate source-grounded proposal
attach citations
route proposal through Create workflow
```

This balances efficiency and accuracy.

The expensive extraction/chunking/embedding work happens once. Later concept-specific usage only performs scoped retrieval, reranking, and proposal generation.

---

## RAG Pipeline

The RAG pipeline should be concept-scoped.

Recommended pipeline:

```text
source attachment or source selection
↓
text extraction
↓
chunking
↓
metadata tagging
↓
embedding
↓
retrieval by concept/query/module request
↓
reranking
↓
source-grounded scaffold/module proposal
↓
citation/reference links back to source
↓
user approval
↓
route through Create editor/save workflow
```

The retrieval query should be based on:

```text
concept name
aliases
learning request
module plan
existing note sections
existing module IDs
related concepts
approved prerequisites
source unit metadata if provided
```

Phase 5 should not retrieve or analyze unrelated chunks just because they are in the same source.

---

## Large Source Handling

Large sources should be indexed broadly but analyzed narrowly.

Example large sources:

```text
textbooks
long documentation PDFs
large lecture packs
multi-chapter course notes
```

For large sources:

```text
Index broadly once.
Retrieve narrowly per concept.
Analyze only relevant chunks.
Use chapter/page/section constraints when available.
```

If the user provides a source unit, such as a chapter or lecture, retrieval should prioritize that unit.

If the user does not provide a source unit, Studium may infer likely locations.

---

## Source Unit Inference

Phase 5 should attempt to infer the relevant source unit when the user chooses a source but does not specify where the concept appears.

Example:

```text
Concept: Regularization
Source: Hands-On Machine Learning
Source unit: unknown
```

Studium should retrieve likely locations and propose:

```text
Likely source locations:
- Chapter 4, pp. 135–142
- Chapter 5, section on regularization
```

The user should confirm the inferred source location before it is written into metadata.

Source location inference should be:

```text
citation-backed
confidence-scored
user-confirmed
```

It should not be silently treated as fact.

---

## Concept-Source Anchor

Phase 5 should create a concept-source anchor when source analysis identifies where a concept primarily lives inside a source.

A concept-source anchor answers:

> Where in this source does this concept mainly originate or appear?

Example:

```yaml
concept_source_anchor:
  concept_id: concept_stochastic_gradient_descent_a1b2c3
  source_id: source_hands_on_ml_abc123
  display_location: "Hands-On ML, Chapter 4, pp. 120–123"
  unit_type: chapter
  unit: Chapter 4
  page_start: 120
  page_end: 123
  primary_chunk_id: chunk_0042
  confidence: high
  user_confirmed: false
```

When the source pane opens next to the concept note, it should open to this location first.

The concept-source anchor is separate from individual module citations.

---

## Source-Aware Workspace

Phase 5 should add a source-aware workspace to the Create/editor experience.

When a source-aware scaffold is generated, the UI should support a two-pane layout:

```text
Left pane:
concept scaffold / rich editor

Right pane:
read-only source viewer
```

The user should be able to fill the scaffold while reading the source.

The source pane should:

```text
preserve original source view when possible
open to the concept-source anchor by default
allow the user to browse the entire processed source
jump to citations when clicked
highlight cited chunks or source regions
show surrounding context
support all processed text sources
```

The source pane should be read-only in Phase 5.

It should not support source editing or permanent source annotation yet.

---

## Citation Behavior

Source citations should be human-navigable.

Internal chunk IDs may exist, but the user-facing citation should point to a readable source title, unit, page, section, or passage.

Example user-facing citation:

```text
Hands-On ML, Chapter 4, pp. 120–123
```

Internal reference:

```yaml
source_reference:
  source_id: source_hands_on_ml_abc123
  source_title: Hands-On Machine Learning
  unit: Chapter 4
  page_range: 120-123
  chunk_id: chunk_0042
  anchor_type: chunk
```

Clicking a citation should:

```text
open the source pane
jump to the relevant source section/page
highlight the cited chunk or closest available region
show surrounding context
allow the user to keep editing the scaffold
```

If exact PDF-region highlighting is not possible, the fallback should be:

```text
jump to the relevant page
show the cited extracted passage in a citation card
highlight the closest available context
```

---

## Module-Level vs Prompt-Level Source References

Source references can exist at two levels.

### Module-Level References

A module-level reference means the entire scaffold module was informed by one or more source chunks.

Example:

```yaml
scaffold_modules:
  - id: module_sgd_worked_example_001
    type: worked_example
    title: Manual SGD Update
    source_references:
      - source_id: source_hands_on_ml_abc123
        display_location: "Hands-On ML, Chapter 4, pp. 120–123"
        chunk_id: chunk_0042
        relevance: primary_support
```

This means:

```text
The module as a whole is supported by this source location.
```

### Prompt-Level References

A prompt-level reference means a specific prompt, blank, or subsection inside the scaffold was generated from a specific source passage.

Example:

```md
### Step 2: Compute the gradient

Use the source’s one-example setup to compute the gradient. [Hands-On ML, Ch. 4, pp. 121–122]
```

This means:

```text
This particular scaffold prompt is directly supported by this cited source location.
```

Recommended rule:

```text
Module-level source references are always stored for source-grounded modules.
Prompt-level clickable citations are used when a specific scaffold prompt or update is directly based on a specific source passage.
```

This avoids over-citing every line while preserving traceability.

---

## Citation Storage and Markdown Behavior

In-app editor behavior:

```text
show clickable citation markers/chips by default
```

Saved Markdown behavior:

```text
omit inline citations by default unless the user toggles them on
```

Metadata behavior:

```text
always preserve source references in module metadata
```

This keeps Markdown notes clean while allowing Studium to reopen the source-linked experience later.

If the user enables inline citations, citations should be saved into the Markdown body.

---

## Source-Grounded Proposal Requirements

Any source-grounded proposal must include source references.

A source-grounded module, update, or relationship should not be presented as source-supported unless the retrieved chunks support it.

Proposal citations should be required per proposed update.

Examples of updates requiring citations:

```text
create new worked example module
add content to existing conceptual explanation module
update relationship based on source
add source-supported prerequisite
add source-supported comparison
```

If the agent suggests something useful but cannot support it from the retrieved source, it should be labeled as:

```text
agent suggestion
```

not:

```text
source-supported
```

---

## Accuracy Guardrails

Phase 5 should include strict accuracy guardrails.

Rules:

```text
Do not claim the source says something unless retrieved chunks support it.
Separate source-supported claims from agent interpretation.
Cite source chunks in proposals.
Mark low-confidence or unsupported areas.
Do not silently overwrite existing notes.
Do not analyze irrelevant source sections.
Do not treat inferred source locations as confirmed without user approval.
```

The proposal should distinguish:

```text
source-supported update
agent-suggested update
user-provided summary
unsupported / needs confirmation
```

---

## Source-Aware New Concept Creation

When creating a new concept note from a source, Phase 5 should allow the scaffold modules to take the source into account.

Example:

```text
Concept: Stochastic Gradient Descent
Source: Hands-On Machine Learning
Learning request: blank
```

Studium should:

```text
select existing source or process new source
retrieve SGD-relevant chunks
infer likely source location
propose module plan
generate source-grounded scaffold modules
attach source references
open source-aware workspace
route through Create editor/save workflow
```

The generated modules should still be scaffold-first, not summary-first.

The source should improve the scaffold by providing:

```text
accurate terminology
source-specific examples
relevant formulas
important distinctions
source-supported relationships
source-supported prerequisites
```

---

## Source-Aware Updates to Existing Notes

When a concept note already exists and the user attaches a new source encounter, Phase 5 should compare the source against the existing note at the module level.

It should not automatically create new modules every time.

Possible update categories:

```text
add_to_existing_module
create_new_module
update_relationships
update_source_encounter_summary
no_new_contribution_detected
```

Example:

```text
Existing note: Stochastic Gradient Descent
Existing modules:
- Conceptual Explanation
- Worked Example
- Code Implementation

New source: OMSCS ML Lecture 3
```

Possible proposal:

```text
Add to existing Conceptual Explanation:
- source gives a clearer intuition for noisy gradients

Create new Comparison module:
- source contrasts SGD with batch gradient descent

Add to existing Worked Example:
- source includes a useful one-step update example

No contribution detected:
- no code implementation discussion found
```

The user should approve updates before anything routes into the Create editor.

---

## Determining What to Add From a Source

Phase 5 should map retrieved source chunks to scaffold module types.

Examples:

```text
definition / intuition → conceptual_explanation
numerical walkthrough → worked_example
code / API / implementation details → code_implementation or implementation_notes
comparison language → comparison
derivation steps → derivation
real-world use → application
common mistake / correction → misconception_debugging
```

Then it should compare those chunks against existing modules.

For each chunk or group of chunks, Studium should decide:

```text
already covered
enrich existing module
create new module
update relationship
ignore as irrelevant
mark unsupported / low confidence
```

This comparison should be proposal-based.

The user should decide what gets added.

---

## Custom Module Focus From User Query

Phase 5 should allow source-aware custom module focus when the user’s learning request asks for it.

Example:

```text
Concept: SGD
Source: Hands-On ML
Learning request: Focus on learning rate schedules.
```

Studium may propose:

```text
Module type: conceptual_explanation
Title: Learning Rate Schedules in SGD
```

or:

```text
Module type: worked_example
Title: Comparing Learning Rates in SGD
```

The module type should still come from the predefined module types.

The title/focus can be custom.

If the user only provides source + concept with no special learning request, Studium should use the source to enrich default/predefined modules rather than inventing many custom modules.

---

## Source-Supported Relationships and Prerequisites

Phase 5 may propose relationships and prerequisites based on source content.

Phase 2/Create can infer prerequisites from graph and agent reasoning.

Phase 5 can strengthen or correct those inferences when the source explicitly supports them.

Rule:

```text
agent-inferred relationship:
allowed, but labeled as agent-inferred

source-supported relationship:
higher confidence if retrieved chunks explicitly support it

conflict:
show both and ask user; do not silently overwrite
```

Example:

```yaml
relationship_candidate:
  type: depends_on
  target: Chain Rule
  confidence: high
  support:
    - source_id: source_backpropagation_notes
      display_location: "Lecture 5, p. 3"
      chunk_id: chunk_0042
      support_type: source_supported
```

Source-supported relationships should still require user approval before being written.

---

## Source Encounter Status Updates

Phase 5 should update learning encounter statuses as source content is processed and used.

Possible transitions:

```text
source_attached → source_analyzed
source_analyzed → integrated
source_analyzed → no_new_contribution_detected
```

Definitions:

```text
source_analyzed:
source has been processed and compared against the concept or scaffold request

integrated:
user approved source-grounded proposals and saved them through Create

no_new_contribution_detected:
source was analyzed, but no meaningful new module/update was found
```

Avoid using the term:

```text
redundant
```

because it may sound dismissive or overconfident.

---

## Cost and Latency Strategy

Phase 5 should be designed to reduce unnecessary cost and latency.

The user should not have to choose between “quick scan” and “deep analysis.”

Instead, the system should use one source-aware analysis flow that is internally efficient.

Efficiency rules:

```text
process source once
reuse chunks and embeddings
retrieve only concept-relevant chunks
use source unit constraints when available
rerank a small candidate set
avoid full-source analysis unless necessary
avoid separate full source analysis report
avoid extra agent passes when a compact proposal is enough
```

Phase 5 should avoid requiring a separate source analysis report before scaffold generation.

Instead, the source-grounded proposal should include a compact evidence summary.

Example:

```text
Recommended addition:
Add worked example module using source example on pages 120–122.

Evidence:
Hands-On ML, Chapter 4, pp. 120–122.
```

This provides transparency without doubling the number of agent calls.

---

## Source Analysis Report Boundary

Phase 5 should not require a separate source analysis report as a normal step.

A separate report could add too much latency.

Instead, source analysis should be integrated into the proposal.

The proposal should include:

```text
recommended updates
evidence/citations
confidence
source-supported vs agent-suggested labels
warnings
```

A full source analysis report may become a future enhancement.

---

## Imported Notes as Sources

Imported notes should be treated like source material.

Example:

```text
Source type: imported_note
File: old_sgd_notes.md
```

Phase 5 can:

```text
extract user-authored content
retrieve relevant sections
generate scaffold modules from it
preserve useful examples
identify possible gaps
attach source references
```

The imported note is not automatically transformed into a final Studium note.

It is source material used to generate or improve scaffold modules.

---

## Future Imported Note + External Source Pairing

A future enhancement may allow the user to upload both:

```text
their old notes
```

and:

```text
the original source those notes came from
```

Then Studium could compare:

```text
what the user captured
```

against:

```text
what the source contains
```

and generate a more complete scaffold.

Example future workflow:

```text
Upload handwritten lecture notes
Upload lecture slides/textbook source
Studium extracts both
Studium identifies gaps in user notes
Studium generates scaffold modules to fill missed concepts
```

This is valuable, but it is not core Phase 5 v1.

It is better suited as a future enhancement or productization feature.

---

## No Direct Note Mutation

Phase 5 should not write directly to concept notes.

It should produce source-grounded proposals.

Those proposals should route through:

```text
Create proposal
↓
Create editor
↓
User approval
↓
Save to Vault
```

This keeps the workflow consistent and prevents silent source-based overwrites.

---

## Build Work

Implement Source Content Intelligence.

This should include:

- Source Library
    
- source upload and storage
    
- source picker for existing sources
    
- source record metadata
    
- source processing statuses
    
- text extraction for supported formats
    
- PDF text extraction for RAG backend
    
- PDF viewer preserving original layout
    
- chunking
    
- source location metadata
    
- embeddings
    
- chunk retrieval
    
- reranking
    
- concept-scoped retrieval
    
- source unit inference
    
- concept-source anchors
    
- source-aware workspace
    
- read-only source pane
    
- citation click behavior
    
- PDF page jump behavior
    
- fallback citation card when exact highlighting is unavailable
    
- module-level source references
    
- prompt-level source references
    
- citation metadata storage
    
- source-grounded proposal generation
    
- source-aware new concept scaffolding
    
- source-aware updates to existing notes
    
- module-level source comparison
    
- source-supported relationship proposals
    
- source encounter status updates
    
- Create workflow integration
    
- latency/cost-conscious retrieval strategy
    

---

## Phase 5 Use Cases

These use cases should be used as implementation checkpoints.

### UC-01: Upload and Process Markdown Source

Input:

```text
Source type: imported_note
File: old_sgd_notes.md
```

Expected behavior:

- source is stored in Source Library
    
- text is extracted
    
- source is chunked and embedded
    
- source record status becomes `ready`
    
- source can be selected later in Create
    

---

### UC-02: Upload and Process PDF Source

Input:

```text
Source type: book
File: hands_on_ml.pdf
```

Expected behavior:

- PDF is stored in Source Library
    
- extractable text is processed for RAG
    
- chunks preserve page/location metadata
    
- PDF remains viewable in original layout
    
- source record status becomes `ready`
    

---

### UC-03: Text-Based Slide PDF Source

Input:

```text
Source type: lecture_slides
File: lecture_3_slides.pdf
```

Expected behavior:

- PDF is accepted if useful text can be extracted
    
- original slide layout is preserved in source viewer
    
- extracted text is used for retrieval
    
- diagrams/images are visible in the PDF viewer even if not deeply analyzed
    

---

### UC-04: Unsupported Image-Only PDF

Input:

```text
Source: scanned handwritten notes PDF
```

Expected behavior:

- system attempts text extraction
    
- if no useful text is found, source status is marked accordingly
    
- user is told OCR/image-heavy support is not reliable yet
    
- source may still be stored, but not used for source-grounded RAG
    

---

### UC-05: Reuse Existing Source

Input:

```text
Concept: Regularization
Source: Hands-On Machine Learning
```

Expected behavior:

- user selects already-uploaded source from Source Library
    
- source is not re-uploaded
    
- existing chunks and embeddings are reused
    
- source-specific retrieval runs for Regularization
    

---

### UC-06: Infer Source Unit

Input:

```text
Concept: Regularization
Source: Hands-On Machine Learning
Source unit: unknown
```

Expected behavior:

- Studium retrieves likely source locations
    
- proposal shows likely chapters/pages/sections
    
- user confirms source unit before metadata is written
    

---

### UC-07: Open Source Pane to Concept Anchor

Input:

```text
Concept: Stochastic Gradient Descent
Source: Hands-On Machine Learning
```

Expected behavior:

- source pane opens to the concept-source anchor
    
- PDF viewer jumps to the relevant chapter/page range
    
- primary cited chunk or closest region is highlighted
    

---

### UC-08: Source-Aware New Concept Scaffold

Input:

```text
Concept: Stochastic Gradient Descent
Source: Hands-On Machine Learning
Learning request:
```

Expected behavior:

- relevant chunks are retrieved
    
- default scaffold modules are generated with source awareness
    
- module references are stored
    
- proposal includes citations
    
- scaffold opens in Create editor with source pane available
    

---

### UC-09: Source-Aware Worked Example

Input:

```text
Concept: Stochastic Gradient Descent
Source: Hands-On Machine Learning
Learning request: Give me a worked example scaffold.
```

Expected behavior:

- source example chunks are retrieved if available
    
- worked example module is proposed
    
- module includes source references
    
- clickable citations open source pane to cited location
    

---

### UC-10: Existing Concept With New Source Encounter

Input:

```text
Existing concept: SGD
New source: OMSCS ML Lecture 3
```

Expected behavior:

- source chunks are retrieved
    
- existing note modules are compared against source
    
- proposal categorizes updates as:
    
    - add_to_existing_module
        
    - create_new_module
        
    - update_relationships
        
    - update_source_encounter_summary
        
    - no_new_contribution_detected
        
- no direct note mutation occurs
    

---

### UC-11: Add Content to Existing Module

Existing note contains:

```text
Conceptual Explanation module
```

New source provides:

```text
clearer intuition for noisy gradients
```

Expected behavior:

- proposal recommends adding content to existing conceptual module
    
- update includes source citation
    
- user approves or rejects before routing through Create
    

---

### UC-12: Create New Module From Source

Existing note lacks:

```text
Comparison module
```

New source contains:

```text
comparison between SGD and batch gradient descent
```

Expected behavior:

- proposal recommends creating a comparison module
    
- module type is predefined
    
- title/focus may be custom
    
- source references are attached
    

---

### UC-13: User Query Creates Focused Module

Input:

```text
Concept: SGD
Source: Hands-On ML
Learning request: Focus on learning rate schedules.
```

Expected behavior:

- retrieval prioritizes source chunks relevant to learning rate schedules
    
- agent proposes focused module using predefined module type
    
- module title may be custom
    
- source references are attached
    

---

### UC-14: No Special User Query Uses Default Modules

Input:

```text
Concept: SGD
Source: Hands-On ML
Learning request:
```

Expected behavior:

- source enriches default module plan
    
- agent does not invent excessive custom modules
    
- proposal stays aligned with predefined scaffold modules
    

---

### UC-15: Clickable Citation Opens Source

User clicks citation:

```text
Hands-On ML, Chapter 4, pp. 120–123
```

Expected behavior:

- source pane opens
    
- PDF jumps to relevant page/section
    
- cited chunk or closest region is highlighted
    
- user can continue editing scaffold
    

---

### UC-16: Citation Fallback Behavior

User clicks citation, but exact PDF region cannot be highlighted.

Expected behavior:

- source pane jumps to relevant page
    
- citation card shows extracted cited passage
    
- closest available context is highlighted or displayed
    

---

### UC-17: App Editor Shows Citation Links

User edits source-aware scaffold in Create.

Expected behavior:

- clickable citation markers are visible in app
    
- clicking them opens corresponding source location
    
- saved Markdown omits inline citations unless user toggles them on
    
- metadata keeps source references regardless
    

---

### UC-18: Source-Supported Relationship Proposal

Source supports:

```text
Backpropagation uses the Chain Rule
```

Expected behavior:

- agent proposes relationship:
    
    - Backpropagation depends_on Chain Rule
        
- relationship is labeled source-supported
    
- proposal includes source citation
    
- user approval is required
    

---

### UC-19: Agent Suggestion Without Source Support

Agent suggests:

```text
Add Learning Rate Schedule module
```

but retrieved chunks do not support it strongly.

Expected behavior:

- suggestion is labeled agent-suggested
    
- not labeled source-supported
    
- user can approve, reject, or request source support
    

---

### UC-20: No New Contribution Detected

Input:

```text
Existing SGD note
New source: short article repeating same information
```

Expected behavior:

- source is processed and compared
    
- no meaningful new module/update is found
    
- learning encounter status may become `no_new_contribution_detected`
    
- no note mutation occurs
    

---

### UC-21: Imported Old Note as Source

Input:

```text
Source type: imported_note
File: old_sgd_notes.md
Concept: SGD
```

Expected behavior:

- old note is treated as source material
    
- relevant sections are retrieved
    
- useful content may be used to generate scaffold modules
    
- imported note is not automatically transformed into a final concept note
    

---

### UC-22: Proposal Routes Through Create

Source Intelligence generates:

```text
source-grounded module proposal
```

Expected behavior:

- proposal routes through Create
    
- user edits in rich editor
    
- user saves through Create workflow
    
- Phase 5 does not directly write to note
    

---

## Outputs

By the end of this phase, Studium should be able to:

- upload source files
    
- store source records in a Source Library
    
- choose existing sources in Create
    
- process supported source types
    
- extract text from supported PDFs
    
- preserve PDF layout in source viewer
    
- chunk and embed source text
    
- reuse processed chunks and embeddings
    
- retrieve concept-relevant source chunks
    
- infer likely source units
    
- create concept-source anchors
    
- open source pane to relevant concept location
    
- generate source-grounded scaffold proposals
    
- compare source content against existing concept modules
    
- propose content additions to existing modules
    
- propose new modules when justified
    
- propose source-supported relationships
    
- attach citations to source-grounded proposals
    
- show clickable citations in the app editor
    
- store citation references in metadata
    
- optionally save inline citations to Markdown
    
- update source and learning encounter statuses
    
- avoid direct note mutation
    
- route proposals through Create
    

---

## Success Criteria

Phase 5 is successful when Studium can use source material to improve scaffolds without becoming slow, expensive, or overconfident.

The user should be able to:

- upload a source once
    
- reuse that source across multiple concepts
    
- choose existing sources from a searchable picker
    
- process PDFs with extractable text
    
- view PDFs in their original layout
    
- create source-grounded scaffolds
    
- open the source beside the scaffold
    
- click citations and jump to the referenced source location
    
- browse the source while filling out the scaffold
    
- use source references without cluttering the saved Markdown
    
- compare a new source encounter against an existing note
    
- receive proposals for missing content or modules
    
- see whether suggestions are source-supported or agent-suggested
    
- approve or reject source-grounded updates
    
- avoid direct automatic note mutation
    

Phase 5 is complete when Studium can process attached or existing source material, retrieve concept-relevant chunks, produce source-grounded scaffold/module proposals with citations, compare sources against existing concept notes for gaps, and pass approved proposals into Create’s editor/save workflow without directly mutating the vault.

---

## Dependencies

- Phase 1: Vault Storage Core
    
- Phase 2: Concept Graph Core
    
- Phase 3: Search
    
- Phase 4: Create
    

---

## Non-Goals

Phase 5 should not include:

- full-source summarization as the primary workflow
    
- source analysis unrelated to a concept/query/module request
    
- direct note mutation
    
- real backlog lifecycle
    
- Agent Review execution
    
- robust OCR for scanned handwritten notes
    
- reliable image-only PDF understanding
    
- full video/audio transcription
    
- complex diagram interpretation
    
- source annotation system
    
- permanent source editing
    
- full contradiction detection
    
- full source comparison reports as required workflow
    
- automatic inline citations in saved Markdown by default
    
- automatic real-vault production use
    

---

## Future Enhancements

- robust OCR for scanned documents
    
- handwritten note extraction
    
- image-heavy PDF understanding
    
- visual diagram interpretation
    
- audio/video transcription
    
- source annotation system
    
- full source analysis reports
    
- imported user notes + authoritative source comparison
    
- gap detection between handwritten notes and lecture/source material
    
- richer PDF region highlighting
    
- source timeline view
    
- source comparison view
    
- citation confidence scoring
    
- local high-performance embedding models
    
- local rerankers
    
- GPU-accelerated source indexing
    
- better latency/cost optimization with stronger local hardware
    
- background source indexing
    
- batch source processing
    
- multimodal source understanding
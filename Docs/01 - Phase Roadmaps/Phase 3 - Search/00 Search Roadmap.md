## Purpose

Build the first user-facing interface for exploring the Studium vault.

Phase 3 exposes the intelligence built in Phase 1 and Phase 2 through a dedicated **Search** tab that allows the user to search for concepts, examples, reflections, sources, broad domains, and semantic clusters.

This phase answers:

> What do I already know, where does it live in my vault, and how is it connected?

The Search tab should combine:

- search bar
    
- ranked results
    
- interactive graph visualization
    
- note preview
    
- source-based filtering/highlighting
    
- relationship navigation
    
- basic navigation history
    
- future handoff stubs to Create and Backlog
    

---

## Why This Phase Comes Here

Search should come before Create because the user needs a way to explore what already exists before creating or modifying anything.

Phase 2 gives Studium the ability to understand concepts, relationships, aliases, sources, and graph neighborhoods. Phase 3 turns that into a usable interface.

This phase helps prevent duplicate notes by making the vault searchable and visually navigable before the full Create workflow exists.

Updated roadmap order:

```text
Phase 1: Vault Storage Core
Phase 2: Concept Graph Core
Phase 3: Search
Phase 4: Create
Phase 5: Source Content Intelligence
Phase 6: Agent Review
Phase 7: Backlog
Phase 8: Retention
Phase 9: Mastery Dashboard
Phase 10: Personal Learning Model 
Phase 11: Productization & Multi-User Platform
```

---

## Planning Work

Define:

- Search tab layout
    
- search query process
    
- query classification rules
    
- ranked result behavior
    
- graph focus behavior
    
- full-vault graph behavior
    
- source search behavior
    
- source hierarchy search behavior
    
- semantic cluster behavior
    
- broad-domain search behavior
    
- no-match behavior
    
- note preview structure
    
- relationship link navigation
    
- graph legend rules
    
- node styling rules
    
- edge styling rules
    
- session-only search history
    
- Search-to-Create handoff stub
    
- Search-to-Backlog handoff stub
    
- required Phase 2 API amendments
    

---

## Search Process

The search flow should follow this process:

```text
User enters query
↓
Studium classifies query type
↓
Studium retrieves ranked results
↓
Studium determines graph focus behavior
↓
Studium updates graph visualization
↓
Studium displays note, source, or cluster preview
↓
User can click related nodes, open in Obsidian, or send result to Create/Backlog
```

Search should not only return text results. It should update the visual graph and preview pane together.

---

## Query Classification

Search should classify user queries into initial query types.

Initial query types:

```text
exact_concept
alias_match
example
reflection
source
broad_domain
semantic_cluster
unknown_or_missing
ambiguous
```

These classifications may change during implementation, but this initial set is enough for Phase 3 planning.

The classification should mostly be internal.

It should only be shown to the user when it changes the experience.

Examples:

```text
Showing source results for Hands-On Machine Learning, Chapter 4.
```

```text
Showing semantic cluster results for Optimization.
```

```text
No exact concept found. Showing related cluster candidates.
```

For obvious exact searches, no extra label is needed.

Example:

```text
Search: SGD
→ Opens Stochastic Gradient Descent
```

---

## Ranked Results

The Search tab should include ranked results in addition to the graph.

Graphs are useful for exploration, but ranked results are better for precision.

Search ranking should prioritize:

1. exact title match
    
2. alias match
    
3. canonical title fuzzy match
    
4. semantic similarity
    
5. relationship/domain relevance
    
6. source match
    

When a user clicks a ranked result, it should behave the same as clicking a graph node.

Expected behavior:

```text
Select result
↓
Center graph on node or cluster
↓
Highlight selected node
↓
Open preview
↓
Add search/view state to session history
```

---

## Graph Visualization

Before the user searches anything, the visualization should show the full vault graph.

For small test vaults, this can show all nodes directly.

The graph should feel dense and exploratory, visually inspired by neural pathways or a brain-like network, but usability should come before aesthetics.

The graph should prioritize:

1. findability
    
2. context
    
3. navigation
    
4. relationship clarity
    

The graph should support:

- zoom
    
- pan
    
- hover to reveal node name
    
- click to open note preview
    
- selected-node highlighting
    
- dimming unrelated nodes
    
- relationship-aware neighborhood display
    
- source highlighting
    
- legend/key for visual encoding
    

---

## Full-Vault View

The default Search view should show the entire vault graph.

In this state:

- node labels are hidden unless hovered
    
- users can zoom and pan manually
    
- related nodes should appear visually closer when possible
    
- obvious relationship structure should be visible through edge styles
    
- clicking a node opens its preview
    
- the graph should not attempt to show mastery state yet
    

For larger vaults, full-node rendering may become too cluttered.

Phase 3 should support or at least prepare for basic cluster abstraction:

```text
Small vault:
show all nodes

Large vault:
show semantic/domain cluster abstractions first
allow search or zoom to expand into actual nodes
```

This does not need to become the full Mastery Dashboard. It is a search-oriented abstraction only.

---

## Focused Search View

When a user searches a specific concept, example, or reflection, the graph should zoom into the relevant cluster.

Example:

```text
Search: SGD
```

Expected behavior:

```text
Stochastic Gradient Descent is centered.
The selected node is highlighted.
Nearby related nodes remain visible.
Unrelated nodes are dimmed.
The note preview opens.
```

If the user searches an example, the graph should center the example node while strongly highlighting the parent concept.

Example:

```text
Search: Manual SGD Computation Example
```

Expected behavior:

```text
Manual SGD Computation Example is centered.
Stochastic Gradient Descent is highlighted as parent concept.
Related concepts remain visible nearby.
The example preview opens.
```

---

## Graph Visual Encoding

The graph should distinguish relationship type through edge style and note type through node style.

Recommended visual model:

```text
Selected/search node:
strong highlight

Relationship type:
edge color or edge style

Note type:
node shape or small icon

Source match:
node glow or highlight

Unrelated nodes:
dimmed

Legend:
visible during focused/search mode
```

Avoid encoding too many meanings with node color alone.

The legend may include:

```text
Selected node
Concept note
Example note
Reflection note
Direct dependency
Prerequisite
Child concept
Parent concept
Variant
Related concept
Source match
Semantic match
Dimmed unrelated node
```

---

## Source Model Amendment

Sources should be searchable through learning encounters.

There should not be a separate top-level `primary_source` abstraction.

Instead, the initial source for a note should be represented as a learning encounter with:

```yaml
role: primary
```

Additional sources should be represented as learning encounters with:

```yaml
role: additional
```

Example:

```yaml
learning_encounters:
  - source:
      type: book
      title: Hands-On Machine Learning
      unit_type: chapter
      unit: Chapter 4
      section:
      link:
    role: primary
    contribution_status: pending
    content_attached: false
    content_id:

  - source:
      type: class
      title: OMSCS Machine Learning
      unit_type: lecture
      unit: Lecture 3
      section:
      link:
    role: additional
    contribution_status: pending
    content_attached: false
    content_id:
```

Search should be able to search across all learning encounters, regardless of whether the encounter is primary or additional.

This means a note created from one source can still appear when searching for a later source encounter.

---

## Source Search

Source should initially be treated as metadata for filtering and highlighting, not as permanent relationship edges between concepts.

Source search should not create permanent graph edges between every note that shares the same source.

Example:

```text
Search: Hands-On Machine Learning
```

Expected behavior:

```text
All notes with a Hands-On Machine Learning learning encounter are highlighted.
All other nodes are dimmed.
The preview panel shows a source result summary.
```

Source result summary should include:

```text
Source title
Source type
Detected units or chapters
Matched concept notes
Matched example notes
Matched reflection notes
Contribution statuses
Links to each matched note
```

---

## Source Hierarchy Search

Sources should support hierarchy when useful.

Examples:

```yaml
source:
  type: book
  title: Hands-On Machine Learning
  unit_type: chapter
  unit: Chapter 4
  section:
  link:
```

```yaml
source:
  type: class
  title: OMSCS Machine Learning
  unit_type: lecture
  unit: Lecture 3
  section:
  link:
```

This allows searches like:

```text
Hands-On Machine Learning
Hands-On Machine Learning Chapter 4
OMSCS Machine Learning Lecture 3
```

If a user searches a book title, Search should show all related notes from that book and allow narrowing into detected chapters.

Example:

```text
Search: Hands-On Machine Learning
```

Result panel:

```text
All concepts from this book

Detected chapters:
- Chapter 2
- Chapter 4
- Chapter 10
```

Clicking Chapter 4 should narrow the graph and result list to notes connected to Chapter 4.

---

## Broad Concept and Semantic Cluster Search

If the user searches a broad concept that does not have an exact note, Studium should try to find a meaningful semantic or relationship cluster.

Example:

```text
Search: Optimization
```

If no exact `Optimization` note exists, but the vault contains related notes, Search may show:

```text
No exact note found for Optimization.
Studium found a related cluster containing Gradient Descent, SGD, Learning Rate, Loss Functions, and Convexity.
```

The graph should show the cluster, not create a permanent note.

Cluster behavior should use:

1. existing domain metadata when available
    
2. parent/child relationships when available
    
3. relationship neighborhoods when available
    
4. semantic similarity as fallback
    

Clusters in Phase 3 are visual/search objects, not durable concept notes.

If the user wants to turn a cluster into a note, they can use the future Create handoff.

---

## No-Match Search

No-match behavior should be separate from broad-concept behavior.

A broad-concept search means:

```text
No exact note exists, but Studium found a meaningful related cluster.
```

A true no-match means:

```text
No matching concept, example, reflection, source, or meaningful cluster was found.
```

For true no-match queries, Search should show:

```text
No matching concept or cluster found.
```

Stub actions:

```text
Send to Create
Send to Backlog
Clear search
```

These buttons should not fully execute Create or Backlog behavior yet. They are handoff stubs for later phases.

---

## Note Preview

The Search tab should include a note preview pane.

When a user selects a node or result, the preview should show:

- title
    
- rendered Markdown preview
    
- relationship links
    
- source information
    
- expandable metadata
    

Metadata should be collapsed by default and expandable when needed.

Metadata may include:

```text
Concept ID
Note type
Note subtype
Status
Aliases
Learning encounters
Relationships
Created at
Updated at
File path
```

Search should not allow direct metadata editing in Phase 3.

If the file path and vault configuration are available, Search should provide:

```text
Open in Obsidian
```

This can use an Obsidian URI or equivalent local-opening behavior later.

---

## Relationship Navigation

Relationships displayed in the preview should be clickable.

Example:

```text
Depends on:
- Chain Rule
- Partial Derivatives
```

Clicking `Chain Rule` should:

```text
Center graph on Chain Rule
Highlight Chain Rule
Open Chain Rule preview
Update session navigation state
```

This behavior should match clicking a graph node or ranked result.

---

## Navigation History

Phase 3 should include basic session-only navigation history.

This history should track looked-up or viewed concepts/searches, not every UI action.

Example:

```text
Search SGD
Search Learning Rate
Go back to SGD
```

History should treat SGD as recently viewed again, similar to how search history works.

Phase 3 should include:

- back/forward navigation state
    
- simple recent searches list
    
- session-only persistence
    

Persisted search history can be a future enhancement.

---

## Search Result Object

Phase 3 should define a structured search result object.

Example:

```yaml
search_result:
  query: "SGD"
  query_type: alias_match

  ranked_results:
    - id: concept_stochastic_gradient_descent_a1b2c3
      title: Stochastic Gradient Descent
      note_type: concept
      match_type: alias
      confidence: high

  graph_focus:
    mode: node_neighborhood
    center_node: concept_stochastic_gradient_descent_a1b2c3
    neighborhood_depth: 1

  preview_target:
    id: concept_stochastic_gradient_descent_a1b2c3
    preview_type: note

  highlighted_nodes:
    - concept_stochastic_gradient_descent_a1b2c3

  dimmed_nodes: []

  suggested_actions:
    - open_in_obsidian
    - send_to_create
    - send_to_backlog
```

Another example for source search:

```yaml
search_result:
  query: "Hands-On Machine Learning Chapter 4"
  query_type: source

  ranked_results:
    - id: concept_stochastic_gradient_descent_a1b2c3
      title: Stochastic Gradient Descent
      note_type: concept
      match_type: source_encounter
      confidence: high

  graph_focus:
    mode: source_highlight
    source:
      type: book
      title: Hands-On Machine Learning
      unit_type: chapter
      unit: Chapter 4

  preview_target:
    preview_type: source_summary

  highlighted_nodes:
    - concept_stochastic_gradient_descent_a1b2c3
    - concept_gradient_descent_b2c3d4

  suggested_actions:
    - narrow_source_unit
    - send_to_create
```

---

## Search-to-Create Handoff

Phase 3 should include a stub button for future Create behavior.

Possible labels:

```text
Send to Create
Create/add scaffold for this concept
```

The button should preserve context for Phase 4.

Example handoff object:

```yaml
handoff:
  target_phase: create
  query: "learning rate in SGD"
  selected_concept_id: concept_stochastic_gradient_descent_a1b2c3
  query_type: exact_concept
  search_context:
    related_nodes:
      - concept_learning_rate_x1y2z3
      - concept_gradient_descent_b2c3d4
    source_filter:
    graph_focus_mode: node_neighborhood
```

The actual Create workflow is implemented in Phase 4.

---

## Search-to-Backlog Handoff

Phase 3 should also include a stub button for future Backlog behavior.

Possible labels:

```text
Send to Backlog
Add as backlog candidate
```

This is useful for:

- no-match searches
    
- broad concepts
    
- missing concepts
    
- concepts the user wants to learn later
    

Phase 3 should not persist backlog items.

The real backlog lifecycle belongs to the Backlog phase.

---

## Phase 2 Amendments Needed

Phase 3 may require small amendments to Phase 2 APIs.

Phase 2 should expose or support:

- ranked concept search
    
- alias search
    
- note type search
    
- source encounter search
    
- source hierarchy search
    
- graph neighborhood query
    
- relationship grouped query
    
- broad-domain or semantic-cluster query
    
- search result confidence
    
- graph focus metadata
    
- note preview metadata extraction
    

The source schema should also be amended so all searchable source information lives inside `learning_encounters`.

The initial source should be represented with:

```yaml
role: primary
```

Additional source encounters should use:

```yaml
role: additional
```

---

## Build Work

Implement the first Search tab.

This should include:

- search bar
    
- query classification
    
- ranked results panel
    
- interactive graph visualization
    
- full-vault graph view
    
- focused graph search view
    
- source-highlight graph mode
    
- basic semantic cluster display
    
- graph legend/key
    
- hover-to-show-node-name behavior
    
- click-node-to-preview behavior
    
- relationship-link navigation
    
- note preview pane
    
- collapsed metadata section
    
- source summary preview
    
- source hierarchy drill-down
    
- Open in Obsidian action when available
    
- session-only navigation history
    
- session-only recent searches
    
- Search-to-Create stub
    
- Search-to-Backlog stub
    
- structured search result object
    

---

## Phase 3 Use Cases

These use cases should be used as implementation checkpoints.

### UC-01: Full Vault Initial Visualization

Before searching, the user opens the Search tab.

Expected behavior:

- entire test vault graph appears
    
- user can zoom and pan
    
- node names appear on hover
    
- clicking a node opens preview
    
- graph does not show mastery state
    

---

### UC-02: Exact Concept Search

Input:

```text
Stochastic Gradient Descent
```

Expected behavior:

- exact concept is ranked first
    
- graph centers on that node
    
- selected node is highlighted
    
- related neighborhood remains visible
    
- note preview opens
    

---

### UC-03: Alias Search

Input:

```text
SGD
```

Expected behavior:

- Search resolves alias to `Stochastic Gradient Descent`
    
- ranked result shows canonical concept
    
- graph centers on canonical concept node
    
- preview opens canonical concept note
    

---

### UC-04: Example Search

Input:

```text
Manual SGD Computation Example
```

Expected behavior:

- example result appears first
    
- graph centers on the example node
    
- parent concept is strongly highlighted
    
- preview shows the example
    
- parent concept link is visible and clickable
    

---

### UC-05: Reflection Search

Input:

```text
Gradient Descent Chapter Reflection
```

Expected behavior:

- reflection result appears first if it matches
    
- related concept nodes are visible nearby
    
- preview opens reflection note
    
- linked concepts are clickable
    

---

### UC-06: Source Search

Input:

```text
Hands-On Machine Learning
```

Expected behavior:

- all notes with a matching learning encounter are highlighted
    
- unrelated nodes are dimmed
    
- result panel lists matching notes
    
- preview pane shows source summary
    
- source is treated as metadata, not permanent relationship edges
    

---

### UC-07: Source Unit Drill-Down

Input:

```text
Hands-On Machine Learning
```

User selects:

```text
Chapter 4
```

Expected behavior:

- results narrow to notes from Chapter 4
    
- graph highlights only Chapter 4 nodes
    
- unrelated source nodes are dimmed
    
- source summary updates to the selected chapter
    

---

### UC-08: Additional Source Encounter Search

A concept was originally created from one source but later received another learning encounter.

Input:

```text
OMSCS Machine Learning Lecture 3
```

Expected behavior:

- notes with that additional learning encounter are highlighted
    
- notes do not need that source as their primary encounter to appear
    
- search uses all learning encounters
    

---

### UC-09: Broad Domain / Semantic Cluster Search

Input:

```text
Optimization
```

No exact Optimization note exists.

Expected behavior:

- Search finds a meaningful related cluster if one exists
    
- graph focuses on the cluster
    
- cluster is temporary, not a permanent note
    
- preview explains that no exact note exists
    
- user sees stub actions for Create or Backlog
    

---

### UC-10: True No-Match Search

Input:

```text
Blue Dolphin Theorem
```

No exact note, source, example, reflection, or meaningful cluster exists.

Expected behavior:

- Search shows no matching concept or cluster found
    
- graph remains unchanged or lightly dimmed
    
- stub actions appear:
    
    - Send to Create
        
    - Send to Backlog
        
    - Clear search
        

---

### UC-11: Ambiguous Query

Input:

```text
Optimization
```

If multiple clusters or meanings are plausible.

Expected behavior:

- Search displays possible interpretations
    
- user chooses one
    
- graph focuses on selected interpretation
    
- no note is automatically created
    

---

### UC-12: Relationship Link Navigation

User opens the preview for Backpropagation and clicks:

```text
Chain Rule
```

Expected behavior:

- graph centers on Chain Rule
    
- Chain Rule node is highlighted
    
- Chain Rule preview opens
    
- navigation history updates
    

---

### UC-13: Ranked Result Click Navigation

User searches:

```text
Gradient
```

Then clicks `Gradient Descent` from ranked results.

Expected behavior:

- graph centers on Gradient Descent
    
- preview opens Gradient Descent
    
- behavior matches clicking a graph node
    

---

### UC-14: Back/Forward Navigation

User views:

```text
SGD
Learning Rate
Gradient Descent
```

Then clicks back.

Expected behavior:

- Search returns to Learning Rate
    
- graph and preview update together
    
- recent search/view state is session-only
    

---

### UC-15: Metadata Preview

User opens a concept preview and expands metadata.

Expected behavior:

- metadata section expands
    
- user can view concept ID, note type, subtype, aliases, sources, relationships, status, and file path
    
- user cannot edit metadata in Search
    

---

### UC-16: Open in Obsidian

User previews a note with known file path.

Expected behavior:

- Open in Obsidian action is available
    
- action opens or points to the note in Obsidian when vault configuration supports it
    

---

### UC-17: Search-to-Create Stub

User searches a missing or existing concept and clicks:

```text
Send to Create
```

Expected behavior:

- Search preserves query and selected context
    
- handoff object is prepared
    
- full Create behavior is not implemented until Phase 4
    

---

### UC-18: Search-to-Backlog Stub

User searches a missing concept and clicks:

```text
Send to Backlog
```

Expected behavior:

- Search preserves query and context
    
- no backlog item is persisted yet
    
- full backlog lifecycle is not implemented until the Backlog phase
    

---

### UC-19: Focused Graph Legend

User searches a concept and the graph focuses on a neighborhood.

Expected behavior:

- selected node is visually distinct
    
- edge styles distinguish relationship types
    
- node styles distinguish note types
    
- source matches can be highlighted
    
- legend explains the visual encoding
    

---

### UC-20: Cluster Abstraction for Larger Vaults

When the vault is too large to display usefully as individual nodes.

Expected behavior:

- Search can use visual cluster abstraction
    
- clusters are based first on existing domain/relationship metadata
    
- semantic clustering is fallback
    
- clusters are not permanent notes
    
- searching can zoom into a cluster’s actual nodes
    

---

## Outputs

By the end of this phase, Studium should be able to:

- display the vault as an interactive graph
    
- search by concept title
    
- search by alias
    
- search by example
    
- search by reflection
    
- search by source
    
- search by source unit such as chapter or lecture
    
- search across all learning encounters
    
- show ranked results
    
- focus graph based on selected result
    
- highlight source matches
    
- dim unrelated nodes
    
- display broad semantic clusters
    
- distinguish broad-cluster search from true no-match search
    
- preview selected notes
    
- show collapsed metadata
    
- navigate through relationship links
    
- maintain session-only navigation history
    
- provide Open in Obsidian action when possible
    
- prepare Search-to-Create handoff context
    
- prepare Search-to-Backlog handoff context
    

---

## Success Criteria

Phase 3 is successful when the user can use Search as the first practical interface into the Studium vault.

The user should be able to:

- open the Search tab and see the vault graph
    
- search for a concept by exact name
    
- search for a concept by alias
    
- search for examples and reflections
    
- search by source
    
- narrow source search by chapter, lecture, or unit
    
- distinguish notes from the searched source from unrelated notes
    
- click ranked results
    
- click graph nodes
    
- click relationships inside note previews
    
- move through recently viewed searches using back/forward navigation
    
- preview notes without editing them
    
- inspect metadata without editing it
    
- open a note in Obsidian when possible
    
- see a semantic cluster when no exact broad concept note exists
    
- see a true no-match state when nothing relevant exists
    
- send search context to future Create or Backlog workflows through stubs
    

Phase 3 is complete when Search can retrieve, visualize, focus, preview, and navigate the vault without creating or modifying notes.

---

## Dependencies

- Phase 1: Vault Storage Core
    
- Phase 2: Concept Graph Core
    

---

## Non-Goals

Phase 3 should not include:

- creating notes
    
- editing notes
    
- editing metadata
    
- generating scaffolds
    
- persistent backlog management
    
- source content analysis
    
- mastery scoring visualization
    
- left-to-right prerequisite mastery map
    
- retention state overlays
    
- personalized next-concept recommendations
    
- automatic permanent cluster note generation
    
- full Create workflow
    
- full Backlog workflow
    

---

## Future Enhancements

- persistent search history
    
- recently viewed note list
    
- advanced filters
    
- saved searches
    
- graph performance optimization
    
- richer cluster abstraction
    
- source timeline view
    
- source comparison view
    
- metadata editing
    
- graph-based note editing
    
- custom graph layouts
    
- search analytics
    
- mastery overlays after Mastery Dashboard exists
    
- automatic video/source recommendation integration
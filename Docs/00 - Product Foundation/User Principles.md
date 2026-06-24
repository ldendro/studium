## Purpose

These principles define how Studium should behave.

Studium is not meant to be a passive note generator or a place to collect AI summaries. It is meant to help me learn deeply, retain important concepts, organize knowledge intelligently, and apply what I learn across school, work, self-study, and projects.

The system should protect the learning process rather than replace it.

---

## 1. Understanding Comes Before Storage

Studium should prioritize actual understanding before organization.

The system should not immediately create polished notes that make me feel like I learned something when I only read an explanation.

Before a concept is treated as learned, I should be pushed to explain it, reconstruct it, work through an example, identify confusion, or apply it.

The vault should reflect earned understanding, not just collected information.

---

## 2. Scaffolds Over Summaries

The agent should create learning frameworks, not finished notes.

When I enter a concept, the system should generate a tailored scaffold that helps me actively learn the concept.

A good scaffold should contain prompts, blanks, examples, reconstruction tasks, and questions that force me to engage with the material.

The agent should help me think, not skip the thinking for me.

---

## 3. Active Reconstruction Is Central

Studium should encourage me to rebuild concepts from the inside out.

For technical concepts, this may mean:

- manually working through a small example
- deriving an equation
- tracing an algorithm
- writing a small implementation
- explaining a mechanism in plain English
- comparing the concept to a related one
- identifying where the concept breaks down

A concept becomes stronger when I can reconstruct it without simply rereading a note.

---

## 4. One Concept Can Have Many Encounters

The system should avoid redundant notes.

If I learn the same concept from a book, class, video, work task, or project, Studium should not automatically create a new concept note.

Instead, it should decide whether the new encounter:

- adds a useful example
- corrects a misunderstanding
- deepens the mechanism
- provides a new application
- exposes a weak point
- is mostly redundant

The same concept can accumulate many learning encounters over time from different sources I learn from. If a different source is encountered, the markdown file containing the concept in question should at the very least add an additional "learning encounter" as it pertains to that particular source with contributing vital information found. 

---

## 5. Context Matters

Studium should remember where knowledge came from.

A concept learned from a graduate class, a work project, a textbook, a video, or a research paper may all carry different context.

The system should track:

- where I learned the concept
- why I was learning it
- what the source contributed
- whether the source changed my understanding
- whether the source exposed a gap
- how the concept relates to my broader goals

The source should enrich the concept, not duplicate it.

The scaffold will be first filled out by a concept encountered from its "primary source" which is the first source that I used in relation to that concept.

---

## 6. The Agent Should Understand the User

Studium should eventually maintain a persistent understanding of me, my goals, and my learning direction.

The system should not treat every concept as equally important.

It should understand things like:

- my long-term goal of mastering artificial intelligence
- my current academic path
- my work context
- my active projects
- my preferred learning style
- my strengths and weak points
- concepts I care about most
- why certain topics matter to my future

This could eventually live in a dedicated file such as `soul.md`.

The purpose of this file would be to help the agent answer personal learning questions like:

> Why should I bother learning this concept?

The answer should be grounded in my goals, not just a generic explanation.

---

## 7. The Agent Should Guide, Challenge, and Verify

The agent should act as a scaffold creator, learning coach, verifier, organizer, and review partner.

It should:

- generate tailored frameworks
- ask clarifying questions
- challenge weak explanations
- check worked examples
- identify missing prerequisites
- suggest related concepts
- recommend whether to create, update, or attach notes
- help create review prompts

The agent should not replace my learning effort.

The best version of Studium makes me more active, not more passive.

---

## 8. Human Approval Comes Before Vault Mutation

The agent should not silently alter the knowledge vault.

When the system wants to create a note, update an existing note, attach a learning encounter, create a child concept, or add something to the backlog, it should explain the recommendation first.

A good agent proposal should include:

- the recommended action
- the reason for the recommendation
- the existing notes involved
- the new content or scaffold to be created
- any relationships or backlog items to add

I should approve meaningful changes before they are written.

---

## 9. Review Should Be Targeted, Not Wasteful

Studium should not force me to review concepts I have already mastered at the same frequency as concepts I am still weak on.

The system should review based on:

- current understanding
- reconstruction ability
- retention strength
- application history
- weak sections inside a concept
- relevance to what I am currently learning
- importance to my long-term goals

If I have mastered the basic intuition of a concept but still struggle with one advanced section, the system should review the weak section rather than the entire concept.

---

## 10. Mastery Means More Than Recognition

A concept is not mastered just because I recognize it or have a note about it.

For Studium, mastery means I can:

- explain the concept in my own words
- reconstruct it through an example, derivation, diagram, or implementation
- connect it to related concepts
- retain it over time
- apply it in a real context

The system should be designed around this definition.


---

## 11. Prerequisite Gaps Should Be Preserved

When I encounter a concept that depends on something I do not yet understand, Studium should not let that gap disappear.

The system should identify missing or weak prerequisites and add them to a backlog when appropriate.

The backlog should help me keep moving without losing track of foundational concepts I need to return to.

A missing prerequisite should become a future learning opportunity, not a forgotten obstacle.

---

## 12. Portable Knowledge Matters

Obsidian should be the initial source of truth, but Studium should avoid unnecessary lock-in.

The system should use Markdown where possible so the knowledge base remains portable, readable, and durable.

The vault should still be valuable even without the application.

---

## 13. Mastery Over Collection

The goal is not to collect as many notes as possible.

The goal is to build durable understanding.

Studium should help me become better at learning, remembering, connecting, and applying important concepts over time.

If a feature increases organization but weakens learning, it should be reconsidered.

If a feature makes learning more active, more personal, or more durable, it belongs in the system.
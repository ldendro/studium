## Vision

Studium is a personal AI-assisted learning system designed to help me deeply learn, organize, retain, and apply concepts over time. A wealth of education has been unlocked for the average person with the advent of LLM/LMMs, and Studium is meant to harness this potential to make me a bonafide expert in what I pursue. Consider Studium in its most simplest abstraction as a Modern Learning OS. 

The system exists because current AI tools are powerful at explaining information, but they often skip the part where real learning happens: active note-taking, reconstruction, working through examples, correcting misunderstandings, connecting ideas, and reviewing knowledge over time. The project is meant to combine the effectiveness of a normal chatbot in explaining information with the typical principles/methodologies of actually learning material, enhanced through AI as a kind of teacher. 

This project should combine the strengths of an AI tutor, an Obsidian-connected second brain, and a long-term knowledge vault. Its purpose is not to generate polished notes for me. Its purpose is to help me build expert-level understanding through smart scaffolds, active reconstruction, concept organization, and persistent mastery tracking.

## Core Problem

AI has made it easier than ever to get explanations, summaries, and answers. But explanations alone do not guarantee learning. I've found myself skimming summaries of questions that I have on topics, and while they are certainly useful in initially understanding something, I don't actually master that concept while doing so.

The missing piece is a hybrid workflow where AI helps structure the learning process without replacing the learner’s effort.

For technical concepts especially, real understanding often comes from:

- writing ideas in my own words
- filling in structured notes while studying
- working through examples manually
- reconstructing equations, algorithms, or mechanisms
- identifying what confused me
- connecting new ideas to old ones
- reviewing weak concepts over time
- applying concepts in real projects or work

Studium should support that full process.

## Product Thesis

The system should help me learn concepts more deeply by generating tailored, fill-in-the-blank-style learning frameworks based on the concept I am studying. The idea is that I'll query a concept I am learning at work, school, books I'm reading, or other related sources and the system will produce a smart scaffold for me to fill in.

Instead of giving me a completed AI-generated note, the system should create an empty or partially guided scaffold that forces me to engage with the material.

For example, if I am learning stochastic gradient descent, the system should not simply explain SGD. It should create a structured note that asks me to define the problem, explain the intuition, work through a small numerical example, compute an update step, identify confusing parts, connect the concept to related ideas, and create future recall prompts. After I fill in the note, the agent will then act as a verifier to validate the notes I took and build upon them. The agent will then act as an organizer connecting the concept i just learned to other related concepts I have learned or should learned (which will be added to a backlog). After that, the agent will act as a review partner on concepts due for a retainment session. 

The agent should act as a scaffold creator, learning coach, verifier, organizer, and eventually a review partner. It should never replace the actual learning process. 

## Initial User

The initial user is me.

This project is being designed for my own long-term learning across:

- graduate coursework
- work
- self-study
- books
- videos
- papers
- technical projects
- AI and machine learning mastery

The system may eventually become useful to others, but it is not initially being designed as a public SaaS product.

## Relationship to Obsidian

Obsidian will be the initial source of truth for the knowledge vault.

The system should create, update, and organize Markdown notes that can live inside an Obsidian vault. However, the system should avoid being permanently locked into Obsidian-specific behavior when possible.

The long-term knowledge base should remain portable, readable, and durable through Markdown.

We can/should incorporate Obsidian plugins where useful for the project.

## What the System Should Do

Mastery System should help me:

1. Enter a concept I am learning.
2. Specify where I am learning it from.
3. Check whether I already have that concept in my vault.
4. Decide whether the concept should become a new note, attach to an existing note, update an existing note, or become a backlog item (there are more possibilities of a concept than just the ones listed)
5. Generate a tailored learning scaffold for the concept.
6. Help me actively reconstruct the concept through examples, derivations, diagrams, code, or explanations.
7. Preserve where I learned the concept and what that source contributed.
8. Connect the concept to related concepts in a meaningful way.
9. Identify prerequisite gaps, which will be added to a backlog of concepts to explore in the future. 
10. Help me review and retain the concept over time.
11. Track progression toward mastery.
12. Help me apply concepts in real contexts.

## What Makes This Different

The immediate differentiator is the creation of tailored learning scaffolds.

The system should not treat every concept the same. A machine learning concept, an algorithm, a mathematical theorem, a system design idea, and a work-related technical lesson may each require a different framework. They should also be labeled according to their origin/purpose in my advancement towards mastery. 

The second immediate differentiator is active reconstruction. The system should push me to work through the concept myself instead of passively accepting an explanation.

Long term, the system becomes more powerful through:

- source-aware concept tracking
- duplicate prevention across repeated learning encounters
- prerequisite backlog management
- relationship-aware concept organization
- retention and review scheduling
- mastery scoring
- AI mastery dashboards

## Definition of Mastery

A concept is not mastered just because I have a note about it.

For this project, mastery means I can:

- explain the concept in my own words
- reconstruct it through an example, derivation, diagram, or implementation
- connect it to related concepts
- retain it over time
- apply it in a real context

The system should be designed around this definition.

## Role of the Agent

The agent should:

- evaluate a new or existing concept in terms of where it belongs in the vault
- scaffold the learning process
- challenge my understanding
- verify my explanations and examples
- identify gaps or misconceptions
- suggest connections to existing concepts
- organize new information into the vault
- help schedule review
- support long-term mastery through an advancing perspective on the user and their goals as the system is used 

The agent should not replace my learning effort.

The best version of this system helps me think more clearly, not think less.

## First Development Phase: Create Tab

The first development phase is the Create tab.

The Create tab is the front door of the system. It should allow me to enter a concept, provide learning context, check the existing vault, detect related concepts or prerequisites, and generate a tailored learning scaffold.

The Create tab should answer the question:

> When I encounter a concept, what should the system help me do with it?

Possible outcomes include:

- create a new concept note
- attach a new learning encounter to an existing concept
- update an existing note
- create a child concept
- add a prerequisite to the backlog
- mark the concept as redundant
- generate a tailored scaffold for active learning

The Create tab must be designed carefully because it determines how knowledge enters the system.

## Non-Goals

Studium is not intended to be:

- a passive AI note generator
- a place to hoard summaries
- a replacement for learning
- a generic chatbot over notes
- a public SaaS product in its initial form

The system should foster learning, not bypass it.

## Guiding Principle

The goal is not to collect more information.

The goal is to build durable understanding.

Studium should help me become better at learning, remembering, connecting, and applying important concepts over time.

## Inspiration

Drawn from Ethan Mollick's Co-Intelligence, specifically the 'AI as a tutor' chapter which showcases the possible advancements in education due to the advent of AI. Studium can help answer the question of **Why should I bother learning this?** as its tailored to a particular user and their goals. 
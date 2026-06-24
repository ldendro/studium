## Core Rule

AI may help me write code, but I am responsible for understanding every branch before moving on.

A branch is not complete just because the code works.  
A branch is complete only when I can explain what changed, why it changed, how it works, and how I verified it.

---

## The Three-Layer Documentation Rule

Use the right documentation layer for the right kind of understanding.

### Code Comments

Use code comments for local, non-obvious implementation reasoning.

Comment when future me might ask:

- Why is this written this way?
    
- What edge case is this protecting against?
    
- Why did we avoid the simpler approach?
    
- What assumption does this code depend on?
    

Do not comment obvious code.

### Branch Docs

Use branch docs for implementation-specific understanding.

Each branch doc should explain:

- what the branch added
    
- why the branch exists
    
- what files changed
    
- the main code flow
    
- what tests or manual checks verified it
    
- what I learned
    
- what I still do not fully understand
    

Branch reflections belong inside the branch doc.

### Concepts

Use `Concepts/` only for reusable technical ideas that appear across multiple branches.

Examples:

- YAML frontmatter
    
- Markdown parsing
    
- SQLite indexing
    
- vector embeddings
    
- RAG chunking
    
- graph traversal
    
- review comment anchoring
    

Do not create concept notes for every small implementation detail.

---

## The No-Blind-Coding Rule

I do not move to the next branch until I can answer these questions:

1. What problem did this branch solve?
    
2. What files changed?
    
3. What is the main flow of the implementation?
    
4. What data structures or schemas were introduced or changed?
    
5. What part of the implementation was generated or suggested by AI?
    
6. What parts did I manually review or improve?
    
7. What tests or manual checks prove this works?
    
8. What do I still not fully understand?
    

If I cannot answer these, the branch is not done.

---

## The 2–3 Minute Explanation Rule

Before considering a branch complete, I should be able to explain it out loud in 2–3 minutes without reading the code line by line.

I should be able to explain:

- the purpose
    
- the main flow
    
- the important files
    
- the important decisions
    
- the verification steps
    

If I cannot explain it simply, I do not understand it well enough yet.

---

## The Documentation Friction Rule

Documentation should support implementation, not slow it down.

For each branch, I only need enough documentation to feel confident moving forward.

Required branch documentation:

- goal
    
- scope
    
- implementation plan
    
- files changed
    
- tests / verification
    
- code understanding notes
    
- branch reflection
    
- merge checklist
    

Avoid duplicating the entire codebase in Obsidian.

---

## The Commenting Rule

Comment code only when the reasoning is not obvious.

Good comments explain why.

Bad comments repeat what the code already says.

A comment is useful if it prevents future misunderstanding.

---

## The Merge Checklist

Before merging or moving on from a branch:

-  I reviewed all AI-generated code.
    
-  I understand the main implementation flow.
    
-  I can explain the branch in 2–3 minutes.
    
-  I know which files changed and why.
    
-  I ran or defined relevant tests.
    
-  I manually verified the expected behavior.
    
-  I documented confusing parts or open questions.
    
-  I updated relevant schemas, roadmap docs, or technical docs if needed.
    
-  I did not leave unexplained code that I cannot defend.
    

---

## Final Principle

AI scaffolds the implementation.  
I reconstruct the understanding.
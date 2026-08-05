## Concept Overview

Recall@K measures the proportion of all relevant items that appear within the system's top $K$ results.
$$
Recall@K = \frac{|relevant\space items \space \cap \space top-K \space results|} {|all \space relevant \space items|}
$$
The $K$ establishes a cutoff. Recall@5 only evaluates the first five retrieved results, even if relevant items appear later. If $K$ is smaller than the total number of relevant items $R$, than Recall@K will always be less than 1. 

### Example

Suppose five notes are relevant to a query:
$$
R = \{{A,B,C,D,E}\}
$$
The top three retrieved notes are:
$$
Top-3 = \{{A,F,C}\}
$$
Two of the five relevant notes were retrieved:
$$
Recall@3 = \frac{2}{5}= 0.40
$$
So the system achieved 40% Recall@3. 
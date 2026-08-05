## Concept Overview

A dense embedding is a compact numerical vector that represents the meaning or learned characteristics of an item, such as a word, sentence, image, or user. 

It is called:
- Dense because most dimensions contain non-zero values
- Embedding because the item is placed within a learned vector space

## Mathematical Formula

An embedding model maps an input $x$ to a $d$-dimensional vector:
$$
f_{\theta}(x) = e_x \in \mathbb{R}
$$
Where:
- $f_\theta$: the learned embedding model
- $x$: the original item
- $e_x$: its embedding
- $d$: the embedding dimensionality 
Similarity is commonly measured using <font color="#c00000">cosine similarity</font>:
$$
cosine(q, d) = \frac{q \cdot d}{||q||||d||}
$$
Interpretation:
- Near 1: Vectors point in similar directions
- Near 0: largely unrelated
- Near -1: vectors point in opposite directions

## Mental Model (High level) for embedding generation

1. Text: 
	1. User query, concept note document, etc
2. Tokens: 
	1. Breaking up the text into a uniform vocabulary the embedding model can digest
3. Initial token vectors: 
	1. Each token ID indexes a learned embedding matrix:
		1. $$ E \in \mathbb{R}^{|v|\times d} $$
		2. Where:
			1. $|V|$: Vocabulary size
			2. $d$: Embedding Dimension
			3. Row $E_t$: learned vector for token $t$
		3. $$ x_i = E[t_i] + p_i $$
		4. A positional embedding $p_i$ is added so the model knows where the token appears. 
		5. At this point, each token has an immediate static initial representation. The word "bank" initially receives the same vector whether it refers to a financial bank or riverbank. 
4. Contextualization through transformer layers
	1. The token passes through multiple transformer blocks. Self-attention allows each token to incorporate information from the other tokens. 
5. Pooling into one vector
	1. The Transformer produces one vector per token, but retrieval generally needs one vector for the entire sentence or document. A pooling operation combines them.
	2. Possible pooling operations include:
		1. **<font color="#c00000">Mean pooling</font>**: Average all contextualized token vectors:
		2. <font color="#c00000">Special-token pooling</font>: Some models add a special token such as $[CLS]$ and use its final representation.
		3. <font color="#c00000">Weight pooling</font>: Tokens can contribute different amounts 
6. Projection and normalization
	1. The pooled representation may pass through a learned projection layer to map it into the desired embedding space or dimensionality. 
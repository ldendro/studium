## Concept Overview 

An embedding space is a multidimensional coordinate system where items, such as words, documents, images, or users, are represented as dense vectors. An embedding model performs the mapping:
$$
f_{\theta}(x)= e_x \in \mathbb{R}^d
$$
where:
- $x$: original item
- $f_\theta$: trained embedding model
- $e_x$: resulting embedding 
- $d$: number of dimensions in the embedding space 
The model learns to arrange vectors so that items with similar learned meanings or properties are positioned near one another. 

## Dimensions in detail

The dimensions are learned features, not usually explicit labels such as:
- [AI, statistics, difficulty]
Meaning is distributed across the complete vector. A concept such as "machine learning" may depend on patterns across hundreds of dimensions. 
- **Rotational Invariance**, where if every vector in an embedding space is rotated in the same way, their relative geometry can remain unchanged when $R$ is an orthogonal rotation matrix. 
  $$ (Rx)^T(Ry)=x^Ty$$
	- Retrieval behavior stays the same even though every coordinate has changes. This indicates that individual aces often have no uniquely correct semantic interpretation; the relationships among vectors matter more. 
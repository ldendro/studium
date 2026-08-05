## Concept Overview 

MRR measures how early the first relevant result appears in a ranked list. 

For each query:
1. Find the rank of its first relevant result.
2. Take the reciprocal of that rank.
3. Average these reciprocal ranks across all queries 

It rewards systems that place at least one correct result near the top.

## Mathematical Formula

For $N$ queries:
$$
MRR = \frac{1}{N}\sum_{i=1}^{N}\frac{1}{rank_i}
$$
Where $rank_i$ is the position of the first relevant result for query $i$. If no relevant result is retrieved, that query receives:
$$
RR_i=0
$$
## Limitation
$MRR$ only considers the first relevant result. It ignores all relevant results appearing after it. Use $MRR$ when the first correct result matters most; use Recall@K when retrieving broader relevant coverage matters.
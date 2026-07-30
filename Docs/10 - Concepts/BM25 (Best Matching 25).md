## Concept Overview

BM25 is a key-word based ranking algorithm that estimates how relevant a document is to a search query. 

Intuitively, a document receives a higher score when:

- It contains the query's important terms. 
- Those terms appear multiple times, although repeated occurrences provide diminishing value. 
- The terms are rare across the overall document collection.
- The document contains the terms densely rather than merely being very long. 

Unlike embedding search, BM25 matches exact terms, not semantic meaning,

## Mathematical Formula 

For query $Q$ and document $D$:
$$
BM25(D,Q) = \sum_{t\in Q} IDF(t) \cdot \frac{f(t, D)k_1 + 1}{f(t, D)+ k_1(1-b+b\frac{|D|}{avghdl})}
$$
Where:
- $t$ : a query term
- $f(t,D)$ : frequency of term $t$ in document $D$
- $|D|$ : document length
- $avgdl$ : average document length in the collection
- $k_1$ : controls how quickly repeated terms lose additional value, usually around 1.2 to 2.0
- $b$ : controls document-length normalization, usually around 0.75

A common inverse document formula $IDF(t)$ is:
$$
IDF(t) = \ln(1 + \frac{N - n(t)+0.5}{n(t) + 0.5})
$$
Where:
- $N$ : total number of documents
- $n(t)$ : number of documents containing $t$

We apply $ln$ to $IDF$ to compress the difference between extremely rare and moderately terms. Without the logarithm, we might use:
$$
IDF(t) = \frac{N}{n(t)}
$$
If there are 10,000 documents:
- A term in 1 document gets 10,000
- A term in 10 documents gets 1,000
- A term in 1,000 documents gets 10
The rarest term would overwhelmingly dominate the score. With:
$$
IDF(t) = \ln (\frac{N}{n(t})
$$
The scores become approximately:
- $ln(10,000)=9.21$
- $ln(1,000)=6.91$
- $ln(10)=2.30$
The rare term remains more informative, but not disproportionately so. 
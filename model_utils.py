import math
import re
from collections import Counter
import numpy as np


class BM25Model:
    """Fast, self-contained BM25 Okapi retrieval model."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lens = []
        self.doc_freqs = {}
        self.idf = {}
        self.tokenized_corpus = []

    def tokenize(self, text: str):
        tokens = re.findall(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*", text.lower())
        return tokens

    def fit(self, corpus):
        self.tokenized_corpus = [self.tokenize(doc) for doc in corpus]
        self.corpus_size = len(corpus)
        self.doc_lens = [len(doc) for doc in self.tokenized_corpus]
        self.avg_doc_len = sum(self.doc_lens) / max(1, self.corpus_size)

        df = Counter()
        for doc in self.tokenized_corpus:
            unique_tokens = set(doc)
            for token in unique_tokens:
                df[token] += 1
        self.doc_freqs = df

        for token, freq in df.items():
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str):
        q_tokens = self.tokenize(query)
        scores = np.zeros(self.corpus_size, dtype=np.float32)

        for token in q_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for doc_idx, doc in enumerate(self.tokenized_corpus):
                term_count = doc.count(token)
                if term_count == 0:
                    continue
                doc_len = self.doc_lens[doc_idx]
                numerator = term_count * (self.k1 + 1)
                denominator = term_count + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_idx] += idf_val * (numerator / denominator)

        return scores

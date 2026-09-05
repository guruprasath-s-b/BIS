import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from model_utils import BM25Model


class BISDomain54Index:
    """Hybrid Semantic + BM25 Retrieval & QA Index for BIS Domain 54."""
    def __init__(self):
        self.bm25 = BM25Model()
        self.tfidf_word = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=25000,
            sublinear_tf=True
        )
        self.tfidf_char = TfidfVectorizer(
            ngram_range=(3, 5),
            analyzer="char",
            max_features=25000,
            sublinear_tf=True
        )
        self.chunks = []
        self.tfidf_word_matrix = None
        self.tfidf_char_matrix = None

    def train_and_index(self, corpus_json_path: Path, output_model_path: Path):
        print(f"Loading corpus from {corpus_json_path}...")
        with open(corpus_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chunks = data["chunks"]
        print(f"Indexing {len(self.chunks)} chunks across {data['metadata']['total_documents']} standards...")

        corpus_texts = []
        for c in self.chunks:
            enriched = f"{c['document_no']} {c['committee']} {c['title']} Page {c['page_number']} : {c['text']}"
            corpus_texts.append(enriched)

        print("Fitting BM25 lexical engine...")
        self.bm25.fit(corpus_texts)

        print("Fitting TF-IDF Word & Char N-Gram vectorizers...")
        self.tfidf_word_matrix = self.tfidf_word.fit_transform(corpus_texts)
        self.tfidf_char_matrix = self.tfidf_char.fit_transform(corpus_texts)

        print(f"Vocabulary sizes: Word TF-IDF = {self.tfidf_word_matrix.shape[1]}, Char TF-IDF = {self.tfidf_char_matrix.shape[1]}")

        model_payload = {
            "chunks": self.chunks,
            "bm25": self.bm25,
            "tfidf_word": self.tfidf_word,
            "tfidf_char": self.tfidf_char,
            "tfidf_word_matrix": self.tfidf_word_matrix,
            "tfidf_char_matrix": self.tfidf_char_matrix,
            "metadata": data["metadata"]
        }

        with open(output_model_path, "wb") as f:
            pickle.dump(model_payload, f)

        print(f"Model successfully trained and saved to {output_model_path} ({output_model_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    base_dir = Path.home() / "Desktop" / "BIS_Domain54"
    corpus_json = base_dir / "corpus_chunks.json"
    output_index = base_dir / "corpus_index.pkl"

    indexer = BISDomain54Index()
    indexer.train_and_index(corpus_json, output_index)

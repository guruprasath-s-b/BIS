import pickle
import re
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from model_utils import BM25Model


class BISRAGEngine:
    """Inference & Question Answering Engine for BIS Domain 54 Standards."""
    def __init__(self, index_path: Path):
        print(f"Loading BIS Domain 54 Index from {index_path}...")
        with open(index_path, "rb") as f:
            data = pickle.load(f)

        self.chunks = data["chunks"]
        self.bm25 = data["bm25"]
        self.tfidf_word = data["tfidf_word"]
        self.tfidf_char = data["tfidf_char"]
        self.tfidf_word_matrix = data["tfidf_word_matrix"]
        self.tfidf_char_matrix = data["tfidf_char_matrix"]
        self.metadata = data["metadata"]
        print(f"Loaded {len(self.chunks)} chunks across {self.metadata['total_documents']} documents.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # 1. Lexical BM25 scoring
        bm25_scores = self.bm25.get_scores(query)
        if np.max(bm25_scores) > 0:
            bm25_scores = bm25_scores / (np.max(bm25_scores) + 1e-6)

        # 2. Dense Word N-gram TF-IDF similarity
        q_word_vec = self.tfidf_word.transform([query])
        word_sims = (self.tfidf_word_matrix @ q_word_vec.T).toarray().ravel()
        if np.max(word_sims) > 0:
            word_sims = word_sims / (np.max(word_sims) + 1e-6)

        # 3. Dense Char N-gram TF-IDF similarity
        q_char_vec = self.tfidf_char.transform([query])
        char_sims = (self.tfidf_char_matrix @ q_char_vec.T).toarray().ravel()
        if np.max(char_sims) > 0:
            char_sims = char_sims / (np.max(char_sims) + 1e-6)

        # 4. Boost exact document or committee matches if mentioned in query
        boosts = np.zeros(len(self.chunks), dtype=np.float32)
        q_clean = query.upper()
        for idx, chunk in enumerate(self.chunks):
            doc_no = chunk.get("document_no", "").upper()
            comm = chunk.get("committee", "").upper()
            if comm and comm in q_clean:
                boosts[idx] += 0.25
            numbers = re.findall(r"\d+", doc_no)
            for num in numbers:
                if len(num) >= 3 and num in q_clean:
                    boosts[idx] += 0.5

        # 5. Hybrid fused score: 40% BM25 + 30% Word TF-IDF + 20% Char TF-IDF + 10% Boost
        final_scores = (
            0.40 * bm25_scores +
            0.30 * word_sims +
            0.20 * char_sims +
            0.10 * boosts
        )

        top_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, start=1):
            chunk = self.chunks[idx]
            score = float(final_scores[idx])
            results.append({
                "rank": rank,
                "score": round(score, 4),
                "document_no": chunk["document_no"],
                "title": chunk["title"],
                "committee": chunk["committee"],
                "page_number": chunk["page_number"],
                "total_pages": chunk["total_pages"],
                "source_file": chunk["source_file"],
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"]
            })

        return results

    def answer_question(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Perform Question Answering over retrieved passages."""
        retrieved = self.search(query, top_k=top_k)
        if not retrieved or retrieved[0]["score"] < 0.05:
            return {
                "query": query,
                "answer": "No relevant standard specification or clause found in Domain 54 for this query.",
                "confidence": 0.0,
                "citations": [],
                "retrieved_passages": []
            }

        primary = retrieved[0]
        context_snippets = []
        citations = []

        for item in retrieved:
            citation = f"{item['document_no']} - {item['title']} (Page {item['page_number']})"
            if citation not in citations:
                citations.append(citation)
            context_snippets.append(item["text"])

        sentences = []
        for snippet in context_snippets:
            for s in re.split(r"(?<=[.!?])\s+", snippet):
                s_clean = s.strip()
                if len(s_clean) > 20:
                    sentences.append(s_clean)

        q_words = set(re.findall(r"\w+", query.lower()))
        scored_sentences = []
        for s in sentences:
            s_words = set(re.findall(r"\w+", s.lower()))
            overlap = len(q_words & s_words)
            if overlap > 0:
                scored_sentences.append((overlap, s))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_answers = [s[1] for s in scored_sentences[:4]]

        if top_answers:
            synthesized_answer = " ".join(top_answers)
        else:
            synthesized_answer = primary["text"][:350] + "..."

        return {
            "query": query,
            "answer": synthesized_answer,
            "confidence": round(min(1.0, primary["score"] * 1.5), 2),
            "top_document": primary["document_no"],
            "top_title": primary["title"],
            "primary_page": primary["page_number"],
            "citations": citations,
            "retrieved_passages": retrieved
        }


if __name__ == "__main__":
    base_dir = Path.home() / "Desktop" / "BIS_Domain54"
    engine = BISRAGEngine(base_dir / "corpus_index.pkl")

    test_q = "What is the test method for extractable tungsten in glass syringes?"
    print(f"\nQuery: {test_q}")
    ans = engine.answer_question(test_q)
    print(f"Answer:\n{ans['answer']}\n")
    print(f"Citations: {ans['citations']}")

import sys
from pathlib import Path
from rag_engine import BISRAGEngine


def main():
    base_dir = Path(__file__).resolve().parent
    index_path = base_dir / "corpus_index.pkl"

    if not index_path.exists():
        print(f"Error: Model index not found at {index_path}. Please run index_model.py first.")
        sys.exit(1)

    engine = BISRAGEngine(index_path)

    print("\n" + "=" * 70)
    print("      BIS DOMAIN 54 (MEDICAL EQUIPMENT & HOSPITAL PLANNING)      ")
    print("                    AI SEARCH & QA ENGINE                       ")
    print("=" * 70)
    print("Ask any question or search for standards, clauses, or tests.")
    print("Type 'exit' or 'quit' to close.\n")

    while True:
        try:
            query = input("Ask a question > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            result = engine.answer_question(query, top_k=3)

            print("\n" + "-" * 70)
            print(f"TOP DOCUMENT : {result.get('top_document', 'N/A')} - {result.get('top_title', '')}")
            print(f"MODE / ROUTE : {result['mode']} / {result['route']}")
            print(f"PAGE REF     : Page {result.get('primary_page', 'N/A')}")
            print("-" * 70)
            print(f"ANSWER:\n{result['answer']}\n")
            print("CITATIONS:")
            for cite in result["citations"]:
                print(f"  • [{cite['id']}] {cite['title']} — {cite['url']}")
            print("-" * 70 + "\n")

        except ValueError as error:
            print(str(error))
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break


if __name__ == "__main__":
    main()

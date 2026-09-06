import time
from pathlib import Path
from rag_engine import BISRAGEngine


def run_benchmark_tests():
    base_dir = Path(__file__).resolve().parent
    index_path = base_dir / "corpus_index.pkl"

    if not index_path.exists():
        print(f"Error: Index file not found at {index_path}. Run index_model.py first.")
        return

    engine = BISRAGEngine(index_path)

    # Ground-truth test suite covering representative standards across Domain 54
    test_cases = [
        {
            "id": "TEST_01",
            "domain": "Hospital Equipment & Disposable Syringes (MHD 12)",
            "query": "How is extractable tungsten determined in glass syringes?",
            "expected_doc_no": "MHD 12 (34618) WC",
            "expected_keywords": ["tungsten", "glass syringes", "extractable", "determination"]
        },
        {
            "id": "TEST_02",
            "domain": "Infusion Sets & Volumetric Controllers (MHD 12)",
            "query": "What are the requirements for infusion sets for single use with volumetric infusion controllers?",
            "expected_doc_no": "MHD 12 (34620) WC",
            "expected_keywords": ["infusion", "volumetric", "controllers", "single use"]
        },
        {
            "id": "TEST_03",
            "domain": "Medical Laboratory Equipment (MHD 10)",
            "query": "What are the vortex mixer specifications for medical laboratory instruments?",
            "expected_doc_no": "MHD 10 (28479) WC",
            "expected_keywords": ["vortex", "mixer", "laboratory"]
        },
        {
            "id": "TEST_04",
            "domain": "Surgical Instruments (MHD 01)",
            "query": "What are the specifications for Mayo pattern scissors dissecting straight and curved on flat?",
            "expected_doc_no": "MHD 1 (34505) WC",
            "expected_keywords": ["mayo", "scissors", "dissecting", "straight", "curved"]
        },
        {
            "id": "TEST_05",
            "domain": "Dentistry & Dental Polymers (MHD 08)",
            "query": "What are the specifications for autopolymerizing acrylic resins for dental use?",
            "expected_doc_no": "MHD 8 (34260) WC",
            "expected_keywords": ["autopolymerizing", "acrylic", "resins", "dental"]
        },
        {
            "id": "TEST_06",
            "domain": "Health Informatics & DICOM (MHD 17)",
            "query": "Digital Imaging and Communication in Medicine DICOM workflow and data management standards",
            "expected_doc_no": "MHD 17 (34655) WC",
            "expected_keywords": ["dicom", "imaging", "communication", "workflow"]
        },
        {
            "id": "TEST_07",
            "domain": "Medical Biotechnology & 3D Printing (MHD 20)",
            "query": "Guidance on additive manufacturing of products for in vivo applications and implantable devices",
            "expected_doc_no": "MHD 20 (32899) WC",
            "expected_keywords": ["additive", "manufacturing", "in vivo", "implantable"]
        },
        {
            "id": "TEST_08",
            "domain": "Needle-Free Injection Systems (MHD 12)",
            "query": "Needle-free injection systems for medical use requirements and test methods",
            "expected_doc_no": "MHD 12 (34619) WC",
            "expected_keywords": ["needle-free", "injection", "test methods"]
        },
        {
            "id": "TEST_09",
            "domain": "Pharmaceutical Packaging & Glass Vials (MHD 12)",
            "query": "What are sterile packaged ready for filling glass vials specifications?",
            "expected_doc_no": "MHD 12 (34623) WC",
            "expected_keywords": ["sterile", "packaged", "filling", "glass vials"]
        },
        {
            "id": "TEST_10",
            "domain": "Veterinary Surgical Instruments (MHD 13)",
            "query": "Veterinary surgical instruments iron pyro-puncture with copper needles",
            "expected_doc_no": "MHD 13 (34744) WC",
            "expected_keywords": ["veterinary", "pyro-puncture", "copper needles"]
        }
    ]

    print("\n" + "=" * 75)
    print("RUNNING BIS DOMAIN 54 MODEL EVALUATION & BENCHMARK SUITE")
    print("=" * 75)

    passed_p1 = 0
    passed_p3 = 0
    reciprocal_ranks = []
    latencies = []

    for test in test_cases:
        t0 = time.perf_counter()
        qa_result = engine.answer_question(test["query"], top_k=3)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

        retrieved = qa_result["retrieved_passages"]
        top_docs = [r["document_no"] for r in retrieved]

        # Calculate rank
        rank = 0
        for i, doc in enumerate(top_docs, start=1):
            if test["expected_doc_no"] in doc or doc in test["expected_doc_no"]:
                rank = i
                break

        is_p1 = (rank == 1)
        is_p3 = (rank > 0 and rank <= 3)

        if is_p1:
            passed_p1 += 1
        if is_p3:
            passed_p3 += 1

        rr = 1.0 / rank if rank > 0 else 0.0
        reciprocal_ranks.append(rr)

        status_str = "PASSED (Rank 1)" if is_p1 else ("PASSED (Top 3)" if is_p3 else "FAILED")

        print(f"\n[{test['id']}] {test['domain']}")
        print(f"  Query: \"{test['query']}\"")
        print(f"  Expected: {test['expected_doc_no']}")
        print(f"  Retrieved Top-1: {retrieved[0]['document_no']} (Score: {retrieved[0]['score']})")
        print(f"  Result: {status_str} | Latency: {elapsed_ms:.1f}ms")
        print(f"  Extracted Answer: {qa_result['answer'][:120]}...")

    total_tests = len(test_cases)
    p1_pct = (passed_p1 / total_tests) * 100
    p3_pct = (passed_p3 / total_tests) * 100
    mrr = sum(reciprocal_ranks) / total_tests
    avg_latency = sum(latencies) / total_tests

    print("\n" + "=" * 75)
    print("FINAL MODEL EVALUATION SCORECARD")
    print("=" * 75)
    print(f"Total Benchmark Test Cases : {total_tests}")
    print(f"Precision @ Top-1 (Exact)  : {passed_p1}/{total_tests} ({p1_pct:.1f}%)")
    print(f"Recall @ Top-3             : {passed_p3}/{total_tests} ({p3_pct:.1f}%)")
    print(f"Mean Reciprocal Rank (MRR) : {mrr:.3f} / 1.000")
    print(f"Average Query Latency      : {avg_latency:.2f} ms")
    print(f"Overall Model Health       : {'EXCELLENT (READY FOR PRODUCTION)' if mrr >= 0.9 else 'SATISFACTORY'}")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark_tests()

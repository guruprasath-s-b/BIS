import json
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """Clean header, footer noise and normalize whitespace."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        # Filter common watermark/header noise
        if not l or "BUREAU OF INDIAN STANDARDS" in l.upper() and len(l) < 40:
            continue
        if re.match(r"^Page \d+ of \d+$", l, re.IGNORECASE):
            continue
        cleaned_lines.append(l)
    return " ".join(cleaned_lines)


def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 100):
    """Split text into overlapping semantic passages."""
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive")
    if overlap < 0 or overlap >= max_chunk_size:
        raise ValueError("overlap must be non-negative and smaller than max_chunk_size")
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_chunk_size, len(words))
        chunk_str = " ".join(words[start:end])
        if len(chunk_str.strip()) > 30:
            chunks.append(chunk_str)
        if end == len(words):
            break
        start += (max_chunk_size - overlap)
    return chunks


def extract_all_documents(pdf_dir: Path, output_file: Path):
    from pypdf import PdfReader

    pdf_files = sorted(list(pdf_dir.glob("*.pdf")))
    print(f"Extracting text from {len(pdf_files)} PDF files in {pdf_dir}...")

    all_chunks = []
    doc_summaries = []

    for idx, pdf_path in enumerate(pdf_files):
        filename = pdf_path.name
        # Extract document identifier and title
        match = re.match(r"^(MHD\s+\d+\s*\([^\)]+\)\s*WC)_(.+)\.pdf$", filename, re.IGNORECASE)
        if match:
            doc_no = match.group(1).strip()
            title = match.group(2).strip()
        else:
            doc_no = filename.replace(".pdf", "")
            title = doc_no

        committee_match = re.search(r"MHD\s*(\d+)", doc_no, re.IGNORECASE)
        committee = f"MHD {committee_match.group(1)}" if committee_match else "MHD"

        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            full_doc_text = []

            for page_num, page in enumerate(reader.pages, start=1):
                raw_page_text = page.extract_text() or ""
                cleaned_page = clean_text(raw_page_text)
                if not cleaned_page:
                    continue

                full_doc_text.append(cleaned_page)
                page_chunks = chunk_text(cleaned_page, max_chunk_size=400, overlap=80)

                for c_idx, chunk in enumerate(page_chunks):
                    all_chunks.append({
                        "chunk_id": f"{doc_no}_p{page_num}_c{c_idx+1}",
                        "document_no": doc_no,
                        "title": title,
                        "committee": committee,
                        "page_number": page_num,
                        "total_pages": num_pages,
                        "source_file": filename,
                        "text": chunk
                    })

            doc_summaries.append({
                "document_no": doc_no,
                "title": title,
                "committee": committee,
                "num_pages": num_pages,
                "total_text_len": sum(len(t) for t in full_doc_text),
                "source_file": filename
            })

            print(f"[{idx+1}/{len(pdf_files)}] Processed: {doc_no} ({num_pages} pages, {len(all_chunks)} total chunks)")

        except Exception as e:
            print(f"[{idx+1}/{len(pdf_files)}] Error parsing {filename}: {e}")

    result = {
        "metadata": {
            "total_documents": len(doc_summaries),
            "total_chunks": len(all_chunks)
        },
        "documents": doc_summaries,
        "chunks": all_chunks
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete! Saved {len(all_chunks)} chunks from {len(doc_summaries)} documents to {output_file}")
    return result


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    pdf_dir = base_dir / "PDFs"
    output_json = base_dir / "corpus_chunks.json"
    extract_all_documents(pdf_dir, output_json)

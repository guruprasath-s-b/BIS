import json
import os
import re
import ssl
import time
import urllib.request
import zipfile
from pathlib import Path

# ============================================================
# BIS DOMAIN 54 (MHD - Medical Equipment & Hospital Planning)
# AUTOMATED DOWNLOADER
# ============================================================

BASE_DIR = Path.home() / "Desktop" / "BIS_Domain54"
PDF_DIR = BASE_DIR / "PDFs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://standards.bis.gov.in/',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*'
}


def clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def post_json(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
        return json.loads(resp.read().decode('utf-8'))


def download_pdf(file_path_remote, output_local_path):
    url = "https://standardsadmin.bis.gov.in/master-service//download-file"
    payload = {
        "fileName": file_path_remote,
        "token": None,
        "refreshToken": None,
        "clientId": None,
        "clientSecret": None,
        "sub": None
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as resp:
        data = resp.read()
        if len(data) > 0:
            with open(output_local_path, "wb") as f:
                f.write(data)
            return len(data)
    return 0


def main():
    print("=" * 60)
    print("BIS Domain 54: Medical Equipment & Hospital Planning")
    print("Starting Automated Document Scraper & Downloader...")
    print("=" * 60)

    # 1. Fetch all MHD Committees
    print("\n[1/4] Fetching MHD sectional committees...")
    comm_resp = post_json(
        "https://standardsadmin.bis.gov.in/technical-committee//getWebsiteSectionalCommittee",
        {
            "departmentId": 64,
            "multipleDepartmentIds": [64],
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None
        }
    )

    committees = comm_resp.get("data", [])
    print(f"Found {len(committees)} committees under MHD Department.")

    all_drafts = []
    seen_project_ids = set()

    # 2. Iterate through each committee to find all drafts
    print("\n[2/4] Scanning all committees for active WC drafts...")
    for idx, comm in enumerate(committees):
        c_id = comm.get("committeeId")
        c_enc_id = comm.get("committeeEncId")
        d_enc_id = comm.get("departmentEncId")
        c_name = comm.get("convertedName") or comm.get("committeeName")

        offset = 0
        limit = 50
        while True:
            draft_payload = {
                "typeSelected": 1,
                "offset": offset,
                "limit": limit,
                "multipleDepartmentIds": [64],
                "multipleCommitteeIds": [c_id],
                "encDepartementId": d_enc_id,
                "encCommitteeId": c_enc_id,
                "token": None,
                "refreshToken": None,
                "clientId": None,
                "clientSecret": None,
                "sub": None
            }

            try:
                res = post_json(
                    "https://standardsadmin.bis.gov.in/project-service/getWebsiteWCDraftTechDepartmentWise",
                    draft_payload
                )
                items = res.get("data", [])
                if not items:
                    break

                for item in items:
                    p_id = item.get("projectId")
                    if p_id not in seen_project_ids:
                        seen_project_ids.add(p_id)
                        all_drafts.append(item)

                total = res.get("totalRecord", 0)
                offset += len(items)
                if offset >= total or len(items) < limit:
                    break
            except Exception as e:
                print(f"  Error fetching drafts for committee {c_name}: {e}")
                break

    print(f"\nTotal unique WC draft documents detected in Domain 54: {len(all_drafts)}")

    # 3. Download PDFs for each draft
    print("\n[3/4] Downloading document PDFs...")
    downloaded_count = 0

    for idx, draft in enumerate(all_drafts):
        doc_no = clean_filename(draft.get("documentNumber", f"doc_{idx+1}"))
        title = clean_filename(draft.get("projectTitleInEnglish", "BIS_Standard"))
        project_enc_id = draft.get("projectencId")
        project_id = draft.get("projectId")

        print(f"\n[{idx+1}/{len(all_drafts)}] Processing: {doc_no}")
        print(f"Title: {title[:80]}...")

        # Fetch document list for this project
        doc_payload = {
            "projectEncId": project_enc_id,
            "projectId": project_id,
            "type": 1,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None
        }

        try:
            doc_res = post_json(
                "https://standardsadmin.bis.gov.in/project-service/getIndividualProjectDocumentGuest",
                doc_payload
            )
            docs = doc_res.get("data", [])
            if not docs:
                print("  No document files found for this project.")
                continue

            # Prioritize main draft document (documentCategory == 3)
            main_doc = None
            for d in docs:
                if d.get("documentCategory") == 3:
                    main_doc = d
                    break
            if not main_doc and docs:
                main_doc = docs[0]

            doc_path_remote = main_doc.get("documentPath")
            if not doc_path_remote:
                print("  Missing remote document path.")
                continue

            safe_name = f"{doc_no}_{title}"[:180] + ".pdf"
            output_file = PDF_DIR / safe_name

            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"  Already downloaded: {output_file.name}")
                downloaded_count += 1
                continue

            size = download_pdf(doc_path_remote, output_file)
            if size > 0:
                print(f"  SUCCESS ({size / 1024:.1f} KB): {output_file.name}")
                downloaded_count += 1
            else:
                print(f"  FAILED to download {doc_no}")

            time.sleep(0.5)

        except Exception as e:
            print(f"  Error downloading project {doc_no}: {e}")

    # 4. Create ZIP
    print("\n" + "=" * 60)
    print("[4/4] Creating ZIP archive...")
    print("=" * 60)

    zip_path = BASE_DIR / "BIS_Domain54_Medical_Equipment.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for pdf in PDF_DIR.glob("*.pdf"):
            zipf.write(pdf, arcname=pdf.name)

    print("\n" + "=" * 60)
    print("PROCESS COMPLETED SUCCESSFULLY!")
    print(f"Total PDFs downloaded: {downloaded_count}")
    print(f"PDF directory: {PDF_DIR}")
    print(f"ZIP file path: {zip_path}")
    print(f"ZIP file size: {zip_path.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()

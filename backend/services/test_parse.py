import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parse_service import parse_and_clean

def test_local_pdf():
    # Path to your test PDF
    pdf_path = Path('../../tests/harrytest2.pdf')

    if not pdf_path.exists():
        print(f"❌ Error: Could not find PDF at {pdf_path.resolve()}")
        sys.exit(1)

    print(f"📂 Reading {pdf_path.name}...")
    pdf_bytes = pdf_path.read_bytes()

    print("⚙️  Parsing and cleaning...")
    result = parse_and_clean(pdf_bytes)

    if "error" in result:
        print(f"❌ Error from parser: {result['error']}")
        return

    text = result.get("text", "")
    toc = result.get("full_toc", [])

    print("\n" + "="*40)
    print("📊 PARSING RESULTS")
    print("="*40)
    print(f"TOC Entries Found : {len(toc)}")
    print(f"Extracted Length  : {len(text):,} characters")

    if not text:
        print("\n⚠️ No text was extracted.")
        return

    print("\n" + "-"*40)
    print("📖 PREVIEW: FIRST 500 CHARACTERS (Checking Chapter 1 start)")
    print("-"*40)
    print(text[:500].strip())

    print("\n" + "-"*40)
    print("📖 PREVIEW: LAST 500 CHARACTERS (Checking end boundary)")
    print("-"*40)
    print(text[-500:].strip())
    print("\n" + "="*40)

if __name__ == "__main__":
    test_local_pdf()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.parse_service import parse_and_clean


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

    chapters = result.get("chapters", [])
    toc = result.get("full_toc", [])

    print("\n" + "=" * 60)
    print("📊 PARSING RESULTS")
    print("=" * 60)
    print(f"TOC Entries Found : {len(toc)}")
    print(f"Chapters Extracted: {len(chapters)}")

    if not chapters:
        print("\n⚠️  No chapters were extracted.")
        return

    total_chars = sum(len(ch["text"]) for ch in chapters)
    print(f"Total Text Length : {total_chars:,} characters")

    print("\n" + "-" * 60)
    print("📖 CHAPTER SUMMARY")
    print("-" * 60)
    for ch in chapters:
        text_len = len(ch["text"])
        print(
            f"  Ch {ch['chapter_num']:>2}: {ch['chapter_title']:<40s} "
            f"pages {ch['start_page']+1}-{ch['end_page']}  "
            f"({text_len:,} chars)"
        )

    # Preview first chapter
    first = chapters[0]
    print("\n" + "-" * 60)
    print(f"📖 PREVIEW: FIRST CHAPTER — {first['chapter_title']}")
    print("-" * 60)
    print(first["text"][:500].strip())

    # Preview last chapter
    if len(chapters) > 1:
        last = chapters[-1]
        print("\n" + "-" * 60)
        print(f"📖 PREVIEW: LAST CHAPTER — {last['chapter_title']}")
        print("-" * 60)
        print(last["text"][-500:].strip())

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_local_pdf()

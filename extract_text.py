import io
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image

import image_text

# =========================================================
# CONFIG
# =========================================================
INPUT_DIR = "inputPDF"
OUTPUT_DIR = "output"
OUTPUT_FILE = "output.txt"
MIN_IMAGE_SIZE = 50


def extract_page_hybrid(page, doc, temp_dir: Path) -> str:
    """Extract native page text, then OCR each embedded image via image_text."""
    parts = []

    text = page.get_text().strip()
    if text:
        parts.append(text)

    images = page.get_images(full=True)
    for img_index, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        pil_image = Image.open(io.BytesIO(image_bytes))
        width, height = pil_image.size
        if width <= MIN_IMAGE_SIZE or height <= MIN_IMAGE_SIZE:
            continue

        temp_path = temp_dir / f"page_{page.number + 1}_img_{img_index + 1}.{image_ext}"
        temp_path.write_bytes(image_bytes)

        print(
            f"[INFO] Page {page.number + 1}: running image OCR "
            f"({img_index + 1}/{len(images)})..."
        )
        try:
            ocr_text = image_text.extract_text_image(str(temp_path)).strip()
        except Exception as e:
            print(f"[WARNING] Image OCR skipped (page {page.number + 1}, image {img_index + 1}): {e}")
            continue
        if ocr_text:
            parts.append(
                f"\n[Image text — page {page.number + 1}, image {img_index + 1}]\n{ocr_text}"
            )

    return "\n\n".join(parts)


def extract_pdf(pdf_path: Path) -> str:
    sections = [f"\n{'=' * 60}\nSOURCE: {pdf_path.name}\n{'=' * 60}\n"]

    with pymupdf.open(pdf_path) as doc:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            for page in doc:
                page_num = page.number + 1
                print(f"[INFO] {pdf_path.name} — page {page_num}/{len(doc)}")
                page_text = extract_page_hybrid(page, doc, temp_dir)
                if page_text.strip():
                    sections.append(f"\n--- Page {page_num} ---\n\n{page_text}")

    return "".join(sections)


def is_output_up_to_date(input_dir: Path, output_file: Path) -> bool:
    if not output_file.exists():
        return False

    pdfs = list(input_dir.glob("*.pdf"))
    if not pdfs:
        return True

    output_mtime = output_file.stat().st_mtime
    return all(pdf.stat().st_mtime <= output_mtime for pdf in pdfs)


def main() -> bool:
    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_file = output_dir / OUTPUT_FILE

    if not input_dir.exists():
        print(f"[ERROR] Directory not found: {input_dir}")
        return False

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[WARNING] No PDF files found in {input_dir}")
        return False

    if is_output_up_to_date(input_dir, output_file):
        print(f"[INFO] {OUTPUT_FILE} is up to date. Skipping extraction.")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Extracting text from {len(pdfs)} PDF(s)...")
    combined = []
    for pdf_path in pdfs:
        print(f"\n[INFO] Processing: {pdf_path.name}")
        combined.append(extract_pdf(pdf_path))

    output_file.write_text("".join(combined), encoding="utf-8")
    print(f"\n[SUCCESS] Combined text saved to {output_file}")
    return True


if __name__ == "__main__":
    main()

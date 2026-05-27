import io
import tempfile
from pathlib import Path
import concurrent.futures

import pymupdf
from PIL import Image

import image_text

# =========================================================
# CONFIG
# =========================================================
from config import INPUT_DIR, OUTPUT_DIR, OUTPUT_TEXT, MIN_IMAGE_SIZE
OUTPUT_FILE = OUTPUT_TEXT.name


def extract_page_hybrid(page, doc, temp_dir: Path, skip_ocr: bool = False) -> str:
    """Extract native page text, then OCR each embedded image via image_text in parallel."""
    parts = []

    text = page.get_text().strip()
    if text:
        parts.append(text)

    if skip_ocr:
        return "\n\n".join(parts)

    images = page.get_images(full=True)
    if not images:
        return "\n\n".join(parts)

    def process_image(img_info) -> str | None:
        img_index, img = img_info
        xref = img[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            pil_image = Image.open(io.BytesIO(image_bytes))
            width, height = pil_image.size
            if width <= MIN_IMAGE_SIZE or height <= MIN_IMAGE_SIZE:
                return None

            temp_path = temp_dir / f"page_{page.number + 1}_img_{img_index + 1}.{image_ext}"
            temp_path.write_bytes(image_bytes)

            print(
                f"[INFO] Page {page.number + 1}: running image OCR "
                f"({img_index + 1}/{len(images)})..."
            )
            ocr_text = image_text.extract_text_image(str(temp_path)).strip()
            if ocr_text:
                return f"\n[Image text — page {page.number + 1}, image {img_index + 1}]\n{ocr_text}"
        except Exception as e:
            print(f"[WARNING] Image OCR skipped (page {page.number + 1}, image {img_index + 1}): {e}")
        return None

    # Run image OCR requests concurrently (up to 4 workers to balance rate limits and speed)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        ocr_results = list(executor.map(process_image, enumerate(images)))

    for res in ocr_results:
        if res:
            parts.append(res)

    return "\n\n".join(parts)


def extract_pdf(pdf_path: Path, skip_ocr: bool = False) -> str:
    sections = [f"\n{'=' * 60}\nSOURCE: {pdf_path.name}\n{'=' * 60}\n"]

    with pymupdf.open(pdf_path) as doc:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            for page in doc:
                page_num = page.number + 1
                print(f"[INFO] {pdf_path.name} — page {page_num}/{len(doc)}")
                page_text = extract_page_hybrid(page, doc, temp_dir, skip_ocr=skip_ocr)
                if page_text.strip():
                    sections.append(f"\n--- Page {page_num} ---\n\n{page_text}")

    return "".join(sections)


def main(skip_ocr: bool = False) -> bool:
    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_file = output_dir / OUTPUT_FILE
    cache_dir = output_dir / "cache"

    if not input_dir.exists():
        print(f"[ERROR] Directory not found: {input_dir}")
        return False

    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[WARNING] No PDF files found in {input_dir}")
        return False

    cache_dir.mkdir(parents=True, exist_ok=True)

    any_cache_updated = False
    combined = []

    for pdf_path in pdfs:
        # Cache file name reflects whether OCR was skipped to avoid cache collision
        cache_file = cache_dir / f"{pdf_path.name}_ocr_{not skip_ocr}.txt"
        
        is_cache_valid = False
        if cache_file.exists():
            cache_mtime = cache_file.stat().st_mtime
            pdf_mtime = pdf_path.stat().st_mtime
            if cache_mtime >= pdf_mtime:
                is_cache_valid = True
                
        if is_cache_valid:
            print(f"[INFO] Using cached text for: {pdf_path.name}")
            pdf_text = cache_file.read_text(encoding="utf-8")
        else:
            print(f"\n[INFO] Extracting text (OCR={not skip_ocr}): {pdf_path.name}")
            pdf_text = extract_pdf(pdf_path, skip_ocr=skip_ocr)
            cache_file.write_text(pdf_text, encoding="utf-8")
            any_cache_updated = True

        combined.append(pdf_text)

    # Rebuild output file if caches were updated or output.txt is missing/out-of-date
    rebuild_output = any_cache_updated or not output_file.exists()
    if not rebuild_output:
        output_mtime = output_file.stat().st_mtime
        for pdf_path in pdfs:
            cache_file = cache_dir / f"{pdf_path.name}_ocr_{not skip_ocr}.txt"
            if cache_file.exists() and cache_file.stat().st_mtime > output_mtime:
                rebuild_output = True
                break

    if rebuild_output:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file.write_text("".join(combined), encoding="utf-8")
        print(f"\n[SUCCESS] Combined text saved to {output_file}")
        return True
    else:
        print(f"[INFO] {OUTPUT_FILE} and all caches are up to date. Skipping extraction.")
        return False


if __name__ == "__main__":
    main()

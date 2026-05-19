# pyrefly: ignore [missing-import]
import fitz
# pyrefly: ignore [missing-import]
import pytesseract
# pyrefly: ignore [missing-import]
from PIL import Image
import io
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

PDF_PATH = r"inputPDF"
OUTPUT_DIR = "output"

# For Windows users:
# Uncomment and change path if tesseract is not detected automatically
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================================================
# DETECT PDF TYPE
# =========================================================

def detect_pdf_type(doc):
    """
    Detects whether PDF is:
    - text-based
    - scanned/image-based
    - mixed
    """
    text_pages = 0
    image_pages = 0

    for page in doc:
        text = page.get_text().strip()
        if text:
            text_pages += 1

        images = page.get_images(full=True)
        if images:
            image_pages += 1

    if text_pages > 0 and image_pages == 0:
        return "TEXT_BASED"
    elif text_pages == 0 and image_pages > 0:
        return "SCANNED"
    elif text_pages > 0 and image_pages > 0:
        return "MIXED"

    return "UNKNOWN"

# =========================================================
# EXTRACT NORMAL TEXT
# =========================================================

def extract_text(doc):
    all_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text()
        all_text.append(f"\n\n========== PAGE {page_num + 1} ==========\n\n")
        all_text.append(text)

    return "".join(all_text)

# =========================================================
# EXTRACT IMAGES + OCR
# =========================================================

def extract_images_and_ocr(doc, output_dir: Path, pdf_name: str = ""):
    image_data = []
    images_dir = output_dir / "images"

    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)

        print(f"[INFO] Page {page_index + 1}: {len(images)} images found")

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            prefix = f"{pdf_name}_" if pdf_name else ""
            image_filename = images_dir / f"{prefix}page_{page_index+1}_img_{img_index+1}.{image_ext}"

            # Save image
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            # OCR Processing
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size

            # Only run OCR if the image is reasonably large
            if width > 50 and height > 50:
                ocr_text = pytesseract.image_to_string(image)
            else:
                ocr_text = "[Image too small for OCR]"

            image_data.append({
                "page": page_index + 1,
                "image_path": str(image_filename),
                "ocr_text": ocr_text
            })

    return image_data

# =========================================================
# MAIN
# =========================================================

def main():
    input_dir = Path(PDF_PATH)
    output_dir = Path(OUTPUT_DIR)

    if not input_dir.exists():
        print(f"[ERROR] Directory not found: {input_dir}")
        return False

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    changes_made = False

    # 1. Cleanup old files (deletions)
    current_pdf_stems = {p.stem for p in input_dir.glob("*.pdf")}
    
    for txt_file in output_dir.glob("*.txt"):
        stem = txt_file.stem
        pdf_stem = None
        if stem.startswith("extracted_text_"):
            pdf_stem = stem[len("extracted_text_"):]
        elif stem.startswith("image_ocr_"):
            pdf_stem = stem[len("image_ocr_"):]
            
        if pdf_stem and pdf_stem not in current_pdf_stems:
            print(f"[INFO] Removing orphaned file: {txt_file.name}")
            txt_file.unlink()
            changes_made = True

    for img_file in images_dir.glob("*.*"):
        if "_page_" in img_file.name:
            pdf_stem = img_file.name.split("_page_")[0]
            if pdf_stem not in current_pdf_stems:
                print(f"[INFO] Removing orphaned image: {img_file.name}")
                img_file.unlink()
                changes_made = True

    # 2. Extract new/modified files
    for pdf_path in input_dir.glob("*.pdf"):
        text_output_file = output_dir / f"extracted_text_{pdf_path.stem}.txt"
        ocr_output_file = output_dir / f"image_ocr_{pdf_path.stem}.txt"
        
        # Check if up to date
        if text_output_file.exists() and ocr_output_file.exists():
            pdf_mtime = pdf_path.stat().st_mtime
            if text_output_file.stat().st_mtime > pdf_mtime and ocr_output_file.stat().st_mtime > pdf_mtime:
                print(f"[INFO] Skipping up-to-date PDF: {pdf_path.name}")
                continue

        print(f"\n[INFO] Processing: {pdf_path.name}")
        changes_made = True
        
        with fitz.open(pdf_path) as doc:
            pdf_type = detect_pdf_type(doc)
            print(f"[INFO] PDF Type Detected: {pdf_type}")

            print("[INFO] Extracting text...")
            extracted_text = extract_text(doc)
            with open(text_output_file, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            print("[INFO] Extracting images and running OCR...")
            image_results = extract_images_and_ocr(doc, output_dir, pdf_path.stem)
            
            with open(ocr_output_file, "w", encoding="utf-8") as f:
                for item in image_results:
                    f.write(f"\n\n========== PAGE {item['page']} ==========\n")
                    f.write(f"\nIMAGE: {item['image_path']}\n\n")
                    f.write(item["ocr_text"])
                    f.write("\n" + "="*50 + "\n")

    print("[INFO] Extraction process complete.")
    return changes_made

if __name__ == "__main__":
    main()
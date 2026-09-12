# -*- coding: utf-8 -*-
"""
=============================================================================
             MOBILE & PC COMPATIBLE PDF GENERATOR SOFTWARE
=============================================================================
- Android (Termux / Pydroid 3) এবং Windows PC উভয় জায়গায় চলবে।
- Playwright / Chromium ব্রাউজার দরকার নেই (Pure Python xhtml2pdf ইঞ্জিন)।
- Excel (details2.xlsx) থেকে তথ্য পড়ে স্বয়ংক্রিয়ভাবে ক্লিকযোগ্য ইমেজ লিঙ্ক ও
  কাস্টম ফরম্যাটে A4 PDF তৈরি করবে।
=============================================================================
"""

import os
import sys
import subprocess

# ── Auto-install missing packages ──────────────────────────────────────────
def install_required_packages():
    required = [
        ("openpyxl", "openpyxl"),
        ("pandas", "pandas"),
        ("PIL", "Pillow"),
        ("xhtml2pdf", "xhtml2pdf"),
        ("requests", "requests")
    ]
    for module_name, pip_name in required:
        try:
            __import__(module_name)
        except ImportError:
            print(f"📦 Installing required package: {pip_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            except Exception as e:
                print(f"⚠️ Warning: Could not install {pip_name} automatically: {e}")

install_required_packages()

import random
import string
import datetime
import time
import re
from pathlib import Path
import io

import pandas as pd
import openpyxl
from xhtml2pdf import pisa

# Handle UTF-8 encoding safely on all platforms
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass

# ================== PORTABLE CONFIG ==================
BASE_PATH = Path(__file__).parent.resolve()
EXCEL_PATH = BASE_PATH / "details2.xlsx"

PDF_OUTPUT_DIR = BASE_PATH / "pdf_output"
FINAL_OUTPUT_DIR = PDF_OUTPUT_DIR / "output"

DEFAULT_URI = "https://leakhdrvideo.blogspot.com/2026/06/pdf.html"
# =====================================================


def is_blank(val):
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.lower() == "nan"


def get_random_template_file(folder_path: Path, extensions: list) -> Path:
    """Returns a random file from folder_path matching the given extensions, or None."""
    if not folder_path.exists() or not folder_path.is_dir():
        return None
    files = []
    for ext in extensions:
        files.extend(folder_path.glob(f"*{ext}"))
        files.extend(folder_path.glob(f"*{ext.upper()}"))
    if not files:
        return None
    return random.choice(files)


def update_excel_cell(excel_path: Path, row_idx: int, col_idx: int, value: str):
    """Safely updates a cell in the excel file with retries if locked."""
    retries = 5
    for attempt in range(retries):
        wb = None
        try:
            wb = openpyxl.load_workbook(str(excel_path))
            sheet = wb.active
            # pandas row index 0 corresponds to excel row 2 (row 1 is headers)
            excel_row = row_idx + 2
            # 0-indexed column index corresponds to excel column col_idx + 1
            excel_col = col_idx + 1
            sheet.cell(row=excel_row, column=excel_col, value=value)
            wb.save(str(excel_path))
            return
        except PermissionError:
            print(f"⚠️ [Attempt {attempt+1}/{retries}] Excel file is open. Close {excel_path.name} to allow saving! Retrying in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error updating Excel cell at row {row_idx + 1}, col {col_idx + 1}: {e}")
            break
        finally:
            if wb:
                try:
                    wb.close()
                except Exception:
                    pass


def build_html_document(title: str, date_str: str, image_html_block: str) -> str:
    """
    Creates an HTML document formatted for mobile-friendly pure-python PDF conversion (xhtml2pdf).
    """
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{
            size: a4;
            margin: 20mm;
        }}
        body {{
            font-family: Helvetica, Arial, sans-serif;
            color: #1a1a1a;
            line-height: 1.5;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
        }}
        .container {{
            width: 100%;
        }}
        .title {{
            text-align: center;
            font-size: 22pt;
            font-weight: bold;
            margin-bottom: 14px;
            color: #111111;
        }}
        .date {{
            text-align: center;
            font-size: 12pt;
            font-weight: bold;
            color: #d90429;
            margin-bottom: 20px;
        }}
        .image-container {{
            text-align: center;
            margin: 15px 0;
        }}
        .image-container img {{
            width: 530px;
            max-width: 100%;
            height: auto;
            border: none;
        }}
        a {{
            color: #0066cc;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">{title}</div>
        <div class="date">{date_str}</div>
        {image_html_block}
    </div>
</body>
</html>"""
    return html_template


def convert_html_to_pdf(html_content: str, output_pdf_path: Path, target_url: str = "", doc_title: str = "") -> bool:
    """
    Directly converts HTML string to PDF using pure Python xhtml2pdf,
    attaches clickable URI link annotation, and sets the exact Document Title metadata.
    """
    try:
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            src=io.StringIO(html_content),
            dest=pdf_buffer,
            encoding='utf-8'
        )
        if pisa_status.err:
            return False

        pdf_buffer.seek(0)
        
        import pypdf
        from pypdf.generic import DictionaryObject, NameObject, ArrayObject, FloatObject, TextStringObject

        reader = pypdf.PdfReader(pdf_buffer)
        writer = pypdf.PdfWriter()
        page = reader.pages[0]

        # Attach native clickable link annotation if URL provided
        if target_url:
            link_dict = DictionaryObject({
                NameObject('/Type'): NameObject('/Annot'),
                NameObject('/Subtype'): NameObject('/Link'),
                NameObject('/Rect'): ArrayObject([FloatObject(50), FloatObject(100), FloatObject(545), FloatObject(650)]),
                NameObject('/Border'): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject('/A'): DictionaryObject({
                    NameObject('/S'): NameObject('/URI'),
                    NameObject('/URI'): TextStringObject(target_url)
                })
            })
            page[NameObject('/Annots')] = ArrayObject([link_dict])

        writer.add_page(page)

        # Set exact title in Document Metadata so PDF viewer tab shows the title!
        if doc_title:
            writer.add_metadata({
                NameObject('/Title'): TextStringObject(doc_title)
            })

        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        return True
    except Exception as e:
        print(f"❌ PDF rendering error: {e}")
        return False


def format_body_to_html(raw_text: str) -> str:
    """
    Converts plain text with linebreaks into HTML paragraphs/breaks
    while preserving embedded HTML tags (like image links).
    """
    paragraphs = raw_text.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if p_clean.startswith("<div") and p_clean.endswith("</div>"):
            html_parts.append(p_clean)
        else:
            p_with_br = p_clean.replace("\n", "<br/>")
            html_parts.append(f"<p>{p_with_br}</p>")
    return "\n".join(html_parts)


def process_row_task(idx: int, A: str, B: str, C: str, D: str, E: str, F: str) -> bool:
    """Processes a single task row and generates the PDF."""
    print(f"\n▶ Row {idx + 1} | Keyword='{A}' | Base='{B}'")

    # ── URL: Column F, default if blank ──
    uri_to_add = F.strip() if not is_blank(F) else DEFAULT_URI
    print(f"   🔗 URL: {uri_to_add}")

    # ── Filename ("Username"): Column B slug or Title slug + serial number ──
    serial_num = idx + 1
    if not is_blank(B):
        clean_b = re.sub(r"[^a-zA-Z0-9_\-]", "-", str(B).strip()).strip("-").lower()
        file_base_name = f"{clean_b}-{serial_num}"
    else:
        clean_slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(E).strip()).strip("-").lower()
        if len(clean_slug) > 35:
            clean_slug = clean_slug[:35].rstrip("-")
        file_base_name = f"{clean_slug or 'viral-video'}-{serial_num}"

    pdf_name = f"{file_base_name}.pdf"
    final_pdf_path = FINAL_OUTPUT_DIR / pdf_name
    print(f"   📄 PDF: {pdf_name}")

    try:
        # ── Body text file selection (Column C) ──
        body_file = None
        if not is_blank(C):
            cleaned_c = str(C).strip().strip('"').strip("'")
            p_c = Path(cleaned_c)
            if p_c.is_file():
                body_file = p_c
            elif (BASE_PATH / cleaned_c).is_file():
                body_file = BASE_PATH / cleaned_c
            elif (BASE_PATH / "viral-body-templete" / cleaned_c).is_file():
                body_file = BASE_PATH / "viral-body-templete" / cleaned_c

        if not body_file:
            body_template_dir = BASE_PATH / "viral-body-templete"
            random_body = get_random_template_file(body_template_dir, [".txt"])
            if random_body:
                body_file = random_body
                print(f"   ℹ️ Column C blank/invalid. Using random template: {body_file.name}")

        if not body_file or not body_file.is_file():
            print(f"   ⚠️ Text template file missing (tried: '{C}') — skipping row")
            return False

        with open(body_file, "r", encoding="utf-8") as fh:
            body_text = fh.read()

        # Perform standard text replacements
        body_text = body_text.replace("keywordss", str(A))
        body_text = body_text.replace("Titleesss", str(E))
        random_num = f"{random.randint(1, 59):02d}"
        body_text = body_text.replace("numberss", random_num)

        # ── Image file selection (Column D) ──
        image_file = None
        if not is_blank(D):
            cleaned_d = str(D).strip().strip('"').strip("'")
            p_d = Path(cleaned_d)
            if p_d.is_file():
                image_file = p_d
            elif (BASE_PATH / cleaned_d).is_file():
                image_file = BASE_PATH / cleaned_d
            elif (BASE_PATH / "viral-image-templete" / cleaned_d).is_file():
                image_file = BASE_PATH / "viral-image-templete" / cleaned_d

        if not image_file:
            fixed_user_path = Path(r"C:\Users\Mizan YT\Music\pdf_output\viral-image-templete\Screenshot 2026-09-09 092247.jpg")
            local_default = BASE_PATH / "default_banner.jpg"
            if fixed_user_path.is_file():
                image_file = fixed_user_path
                print(f"   ℹ️ ফিক্সড ইমেজ ব্যবহার করা হচ্ছে: {image_file.name}")
            elif local_default.is_file():
                image_file = local_default
                print(f"   ℹ️ ফিক্সড ইমেজ ব্যবহার করা হচ্ছে: {image_file.name}")
            else:
                image_template_dir = BASE_PATH / "viral-image-templete"
                image_file = get_random_template_file(image_template_dir, [".png", ".jpg", ".jpeg", ".webp"])
                if image_file:
                    print(f"   ℹ️ Using random template image: {image_file.name}")

        # Construct image HTML block with clickable link (no extra body text)
        # xhtml2pdf needs the raw absolute path (forward slashes), NOT a file:// URI
        if image_file and image_file.is_file():
            abs_image_path = str(image_file.resolve())
            # Use pisa fetchResource workaround: pass path directly (no file://)
            image_html_block = f'''<div class="image-container"><a href="{uri_to_add}"><img src="{abs_image_path}" /></a></div>'''
        else:
            image_html_block = ""

        # Tomorrow's date
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        today_str = tomorrow.strftime("[LAST UPDATED: %B %d, %Y]")

        # Build clean HTML document containing ONLY Title, Date, and Image with link
        html_content = build_html_document(str(E), today_str, image_html_block)

        # Direct HTML to PDF conversion with clickable image link and exact title metadata
        success = convert_html_to_pdf(html_content, final_pdf_path, uri_to_add, str(E))

        if success and final_pdf_path.exists():
            ts_now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"   ✅ [{ts_now}] Done → {pdf_name} ({final_pdf_path.stat().st_size // 1024} KB)")

            # Save the full path to Column G (index 6)
            update_excel_cell(EXCEL_PATH, idx, 6, str(final_pdf_path.resolve()))
            return True
        else:
            print(f"   ❌ Failed to create PDF for row {idx + 1}")
            return False

    except Exception as e:
        import traceback
        print(f"   ❌ Error row {idx + 1}: {e}")
        traceback.print_exc()
        return False


def run_batch_generation():
    """Runs through details2.xlsx and processes pending rows."""
    print("=" * 60)
    print("      🚀 MOBILE & PC PDF GENERATOR (STANDALONE) 🚀")
    print("=" * 60)

    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "viral-body-templete").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "viral-image-templete").mkdir(parents=True, exist_ok=True)

    active_tasks = []
    user_titel_path = BASE_PATH / "Titel" / "titel.txt"
    if user_titel_path.exists():
        titles_file = user_titel_path
    elif (BASE_PATH / "titles.txt").exists():
        titles_file = BASE_PATH / "titles.txt"
    elif (BASE_PATH / "titles_sample.txt").exists():
        titles_file = BASE_PATH / "titles_sample.txt"
    else:
        titles_file = None

    if titles_file.exists():
        with open(titles_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines:
            print(f"📄 '{titles_file.name}' থেকে {len(lines)} টি টাইটেল পাওয়া গেছে।")
            for i, title in enumerate(lines):
                active_tasks.append((i, "", "", "", "", title, DEFAULT_URI))

    if not active_tasks:
        if not EXCEL_PATH.exists():
            print(f"❌ কোনো titles.txt বা {EXCEL_PATH.name} ফাইল পাওয়া যায়নি!")
            print(f"   দয়া করে এই ফোল্ডারে 'titles.txt' অথবা '{EXCEL_PATH.name}' রাখুন।")
            return

        try:
            df = pd.read_excel(EXCEL_PATH)
        except Exception as e:
            print(f"❌ Could not read Excel file: {e}")
            return

        print(f"📊 Loaded {len(df)} rows from {EXCEL_PATH.name}")

        for i, row in df.iterrows():
            G = str(row.iloc[6]) if len(row) > 6 and not pd.isna(row.iloc[6]) else ""
            if not is_blank(G):
                continue

            E = str(row.iloc[4]) if len(row) > 4 and not pd.isna(row.iloc[4]) else ""
            E = E.replace("viral video Viral Video", "Viral Video")
            E = E.replace("video Video", "Video")
            E = E.replace("Viral Viral", "Viral")
            if is_blank(E):
                continue

            A = str(row.iloc[0]) if len(row) > 0 and not pd.isna(row.iloc[0]) else ""
            B = str(row.iloc[1]) if len(row) > 1 and not pd.isna(row.iloc[1]) else ""
            C = str(row.iloc[2]) if len(row) > 2 and not pd.isna(row.iloc[2]) else ""
            D = str(row.iloc[3]) if len(row) > 3 and not pd.isna(row.iloc[3]) else ""
            F = str(row.iloc[5]) if len(row) > 5 and not pd.isna(row.iloc[5]) else ""

            active_tasks.append((i, A, B, C, D, E, F))

    if not active_tasks:
        print("🎉 All rows are already processed or no valid titles found!")
        print(f"📁 Output files are in: {FINAL_OUTPUT_DIR.resolve()}")
        return

    print(f"\n🚀 Total pending tasks: {len(active_tasks)}")
    success_count = 0
    start_time = time.time()

    for task in active_tasks:
        if process_row_task(*task):
            success_count += 1

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print(f"🎉 COMPLETED! Successfully created {success_count}/{len(active_tasks)} PDFs in {elapsed}s")
    print(f"📂 Output Folder: {FINAL_OUTPUT_DIR.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    run_batch_generation()

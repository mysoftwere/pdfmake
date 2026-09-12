import os
import sys
import random
import string
import datetime
import time
from pathlib import Path
import re
import multiprocessing

import pandas as pd
import openpyxl

# Reconfigure stdout/stderr to handle UTF-8 / emojis on Windows without crashing
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass

# ================== PORTABLE CONFIG ==================
base_path = Path(__file__).parent.resolve()
excel_path = base_path / "details2.xlsx"

pdf_output_dir = base_path / "pdf_output"
final_output_dir = pdf_output_dir / "output"

DEFAULT_URI = f"https://viralleak.video/link/?n=pdf-{datetime.datetime.now().strftime('%d')}"
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


def update_excel_cell(excel_path, row_idx, col_idx, value, lock):
    """Safely updates a cell in the excel file under a multiprocessing lock with retries if locked."""
    with lock:
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
                return  # Success, exit function
            except PermissionError:
                print(f"⚠️ [Attempt {attempt+1}/{retries}] Excel file is locked/open in another program. Please close {excel_path.name} to allow saving! Retrying in 3 seconds...")
                time.sleep(3)
            except Exception as e:
                print(f"❌ Error updating Excel cell at row {row_idx + 1}, col {col_idx + 1}: {e}")
                break
            finally:
                if wb:
                    try:
                        wb.close()
                    except Exception:
                        pass


def build_html_document(title, date_str, body_text):
    """Creates a stylized HTML document structured like the original Google Doc."""
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        body {{
            font-family: 'Segoe UI Emoji', 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            color: #1a1a1a;
            line-height: 1.6;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
        }}
        .container {{
            width: 100%;
        }}
        .title {{
            text-align: left;
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 24px;
        }}
        .date {{
            text-align: left;
            font-size: 12pt;
            font-weight: bold;
            color: red;
            margin-bottom: 24px;
        }}
        .body-text {{
            text-align: left;
            font-size: 12pt;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .image-container {{
            text-align: center;
            margin: 10px 0;
        }}
        .image-container img {{
            width: 85%;
            max-width: 100%;
            height: auto;
            border: none;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">{title}</div>
        <div class="date">{date_str}</div>
        <div class="body-text">{body_text}</div>
    </div>
</body>
</html>"""
    return html_template


def process_batch_worker(tasks, worker_name, excel_path, lock):
    """
    Independent worker process that initializes Playwright 
    and processes its list of tasks sequentially.
    """
    from playwright.sync_api import sync_playwright

    print(f"🚀 {worker_name} started — {len(tasks)} task(s)")
    
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        print(f"✅ {worker_name} Playwright browser initialized.")
    except Exception as e:
        print(f"❌ {worker_name} Browser Launch Failed: {e}")
        return

    try:
        for idx, A, B, C, D, E, F in tasks:
            print(f"\n▶ {worker_name} | Row {idx+1} | A='{A}' | B='{B}'")

            # ── URL: Column F, default if blank ──
            uri_to_add = F.strip() if not is_blank(F) else DEFAULT_URI
            print(f"   🔗 URL: {uri_to_add}")

            # ── Filename: Column B + 2 random digits, prefix if blank ──
            if not is_blank(B):
                clean_b = re.sub(r"[^a-zA-Z0-9_\-]", "", str(B).strip())
                two_digits = str(random.randint(10, 99))
                file_base_name = f"{clean_b}{two_digits}"
            else:
                raw_e_clean = re.sub(r"[^a-zA-Z]", "", str(E))
                prefix_e = raw_e_clean[:10].upper()
                needed_random = 25 - len(prefix_e)
                suffix_random = "".join(random.choices(string.ascii_letters + string.digits, k=needed_random))
                file_base_name = f"{prefix_e}{suffix_random}"

            pdf_name = f"{file_base_name}.pdf"
            final_pdf_path = final_output_dir / pdf_name
            print(f"   📄 PDF: {pdf_name}")

            try:
                # ── Body text file selection (Column C) ──
                body_file = None
                if not is_blank(C):
                    cleaned_c = str(C).strip().strip('"').strip("'")
                    p_c = Path(cleaned_c)
                    if p_c.is_file():
                        body_file = p_c
                    elif (base_path / cleaned_c).is_file():
                        body_file = base_path / cleaned_c
                    elif (base_path / "viral-body-templete" / cleaned_c).is_file():
                        body_file = base_path / "viral-body-templete" / cleaned_c

                if not body_file:
                    body_template_dir = base_path / "viral-body-templete"
                    random_body = get_random_template_file(body_template_dir, [".txt"])
                    if random_body:
                        body_file = random_body
                        print(f"   ℹ️ Column C blank/invalid. Using random template: {body_file.name}")

                if not body_file or not body_file.is_file():
                    print(f"   ⚠️ Text template file missing (tried: '{C}') — skipping row")
                    continue

                with open(body_file, "r", encoding="utf-8") as fh:
                    body_text = fh.read()

                # Perform standard replacements
                body_text = body_text.replace("keywordss", A)
                body_text = body_text.replace("Titleesss", E)
                random_num = f"{random.randint(1, 59):02d}"
                body_text = body_text.replace("numberss", random_num)

                # ── Image file selection (Column D) ──
                image_file = None
                if not is_blank(D):
                    cleaned_d = str(D).strip().strip('"').strip("'")
                    p_d = Path(cleaned_d)
                    if p_d.is_file():
                        image_file = p_d
                    elif (base_path / cleaned_d).is_file():
                        image_file = base_path / cleaned_d
                    elif (base_path / "viral-image-templete" / cleaned_d).is_file():
                        image_file = base_path / "viral-image-templete" / cleaned_d

                if not image_file:
                    image_template_dir = base_path / "viral-image-templete"
                    random_img = get_random_template_file(image_template_dir, [".png", ".jpg", ".jpeg", ".gif", ".webp"])
                    if random_img:
                        image_file = random_img
                        print(f"   ℹ️ Column D blank/invalid. Using random template image: {image_file.name}")

                # Replace Imagesvsd with image block if image exists
                # Clean up extra newlines/whitespace around Imagesvsd in the template text
                # to avoid massive gaps when using white-space: pre-wrap.
                pattern_imagesvsd = r'(?:\s*\n)?\s*Imagesvsd\s*(?:\n\s*)?'
                if image_file and image_file.is_file():
                    img_url = image_file.resolve().as_uri()
                    image_html = f'''<div class="image-container"><a href="{uri_to_add}"><img src="{img_url}" /></a></div>'''
                    body_text = re.sub(pattern_imagesvsd, f'\n{image_html}\n', body_text, flags=re.IGNORECASE)
                else:
                    body_text = re.sub(pattern_imagesvsd, '\n', body_text, flags=re.IGNORECASE)

                # Format date to match tomorrow's date
                tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                today_str = tomorrow.strftime("[LAST UPDATED: %B %d, %Y]")

                # Build full HTML doc
                html_content = build_html_document(E, today_str, body_text)

                # Save HTML to a temporary file in output folder
                temp_html_path = final_output_dir / f"temp_{worker_name}_{idx}.html"
                with open(temp_html_path, "w", encoding="utf-8") as fh:
                    fh.write(html_content)

                # Render inside Playwright
                page.goto(temp_html_path.resolve().as_uri())
                page.pdf(
                    path=str(final_pdf_path),
                    format="A4",
                    print_background=True,
                    margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"}
                )

                # Clean up temporary HTML file
                if temp_html_path.exists():
                    try:
                        temp_html_path.unlink()
                    except Exception as ex:
                        print(f"   ⚠️ {worker_name}: Failed to delete temp HTML: {ex}")

                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"   ✅ {worker_name} [{ts_now}] Done → {pdf_name}")

                # Save the full path to Column G (index 6)
                update_excel_cell(excel_path, idx, 6, str(final_pdf_path.resolve()), lock)

            except Exception as e:
                import traceback
                print(f"   ❌ {worker_name} Error row {idx}: {e}")
                traceback.print_exc()

    finally:
        try:
            browser.close()
            pw.stop()
        except Exception:
            pass
        print(f"🏁 {worker_name} finished all tasks.")


def main():
    multiprocessing.freeze_support()  # Important for Windows exe

    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure portable template directories exist
    (base_path / "viral-body-templete").mkdir(parents=True, exist_ok=True)
    (base_path / "viral-image-templete").mkdir(parents=True, exist_ok=True)

    if not excel_path.exists():
        print(f"❌ Excel file not found: {excel_path}")
        sys.exit(1)

    df = pd.read_excel(excel_path)
    print(f"📊 Loaded {len(df)} rows from {excel_path.name}")
    print(f"   Columns: {list(df.columns)}")

    lock = multiprocessing.Lock()
    active_tasks = []

    for i, row in df.iterrows():
        # Column G (index 6) = File full path (if exists)
        G = str(row.iloc[6]) if len(row) > 6 and not pd.isna(row.iloc[6]) else ""
        if not is_blank(G):
            print(f"⏭️ Skipping Row {i+1}: Column G already filled -> {G}")
            continue

        # Column E (index 4) = title (Mandatory: only make PDF if E is present)
        E = str(row.iloc[4]) if len(row) > 4 and not pd.isna(row.iloc[4]) else ""
        E = E.replace("viral video Viral Video", "Viral Video")
        E = E.replace("video Video", "Video")
        E = E.replace("Viral Viral", "Viral")
        if is_blank(E):
            continue

        # Column A (index 0) = keyword
        A = str(row.iloc[0]) if len(row) > 0 and not pd.isna(row.iloc[0]) else ""

        # Column B (index 1) = file name base
        B = str(row.iloc[1]) if len(row) > 1 and not pd.isna(row.iloc[1]) else ""

        # Column C (index 2) = text file path
        C = str(row.iloc[2]) if len(row) > 2 and not pd.isna(row.iloc[2]) else ""

        # Column D (index 3) = image file path
        D = str(row.iloc[3]) if len(row) > 3 and not pd.isna(row.iloc[3]) else ""

        # Column F (index 5) = hyperlink URL
        F = str(row.iloc[5]) if len(row) > 5 and not pd.isna(row.iloc[5]) else ""

        task_data = (i, A, B, C, D, E, F)
        active_tasks.append(task_data)

    if not active_tasks:
        print("🎉 No pending tasks found. All rows are already processed or blank.")
        return

    # Round-robin across 4 workers
    rows_1, rows_2, rows_3, rows_4 = [], [], [], []
    for idx, task_data in enumerate(active_tasks):
        bucket = idx % 4
        if bucket == 0:
            rows_1.append(task_data)
        elif bucket == 1:
            rows_2.append(task_data)
        elif bucket == 2:
            rows_3.append(task_data)
        else:
            rows_4.append(task_data)

    total = len(rows_1) + len(rows_2) + len(rows_3) + len(rows_4)
    print(f"\n🚀 Starting 4-worker multiprocessing | Total rows: {total}")
    print(f"   Worker 1: {len(rows_1)} tasks")
    print(f"   Worker 2: {len(rows_2)} tasks")
    print(f"   Worker 3: {len(rows_3)} tasks")
    print(f"   Worker 4: {len(rows_4)} tasks")

    workers_configs = [
        (rows_1, "Worker-1"),
        (rows_2, "Worker-2"),
        (rows_3, "Worker-3"),
        (rows_4, "Worker-4"),
    ]

    procs = []
    for task_list, w_name in workers_configs:
        if not task_list:
            continue
        p = multiprocessing.Process(
            target=process_batch_worker,
            args=(task_list, w_name, excel_path, lock)
        )
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    print("\n🎉 All processes completed successfully.")


if __name__ == "__main__":
    main()

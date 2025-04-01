import os
import pdfkit
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger

# Configuration for wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# PDF generation options
pdf_options = {
    'enable-local-file-access': None,
    'load-error-handling': 'ignore',
    'disable-javascript': None,
    'quiet': '',
    'encoding': 'UTF-8',
    'margin-top': '15mm',
    'margin-right': '15mm',
    'margin-bottom': '15mm',
    'margin-left': '15mm',
}

def extract_chapter_number(filename):
    """Extract chapter number from filename"""
    base = os.path.splitext(filename)[0]
    parts = base.replace('_', '-').split('-')
    for part in parts:
        if part.isdigit():
            return int(part)
    return 0

def extract_chapter_name(html_path, fallback_name):
    """Extract chapter name from HTML title or filename"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            title = soup.title.string if soup.title else fallback_name
            return title.strip()
    except Exception as e:
        print(f"Could not extract title from {html_path}: {e}")
        return fallback_name.replace('.html', '')

def extract_content_area(html_path):
    """Extract only the content-area div from HTML with proper Korean support"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        content_div = soup.find('div', class_='content-area')
        if not content_div:
            return None
        
        clean_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Malgun Gothic', 'Nanum Gothic', 'NanumMyeongjo', sans-serif;
            line-height: 1.6;
            font-size: 11pt;
        }}
        .content-area {{
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    {content_div.prettify()}
</body>
</html>"""
        return clean_html

def create_toc_pdf(toc_entries, output_pdf):
    """Create a table of contents PDF"""
    html_content = """<html>
<head>
    <meta charset="UTF-8">
    <title>Table of Contents</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; }
        h1 { text-align: center; margin-bottom: 40px; }
        .toc-entry { margin-bottom: 15px; }
        .chapter-number { font-weight: bold; }
        .page-number { float: right; }
    </style>
</head>
<body>
    <h1>Table of Contents</h1>"""
    
    page_num = 3  # Starting after cover and TOC pages
    
    for chapter_num, chapter_name, filename in toc_entries:
        html_content += f"""
    <div class="toc-entry">
        <span class="chapter-number">Chapter {chapter_num}:</span>
        {chapter_name}
        <span class="page-number">{page_num}</span>
    </div>"""
        page_num += 2  # Estimate 2 pages per chapter
    
    html_content += "</body></html>"
    
    pdfkit.from_string(html_content, output_pdf, configuration=config, options=pdf_options)

def create_and_merge_toc(toc_entries, chapter_pdfs, output_pdf):
    """Create TOC and merge with chapter PDFs"""
    toc_pdf = "toc_temp.pdf"
    create_toc_pdf(toc_entries, toc_pdf)
    
    merger = PdfMerger()
    try:
        # Add TOC
        with open(toc_pdf, 'rb') as f:
            merger.append(f)
        
        # Add chapters
        for pdf in chapter_pdfs:
            with open(pdf, 'rb') as f:
                merger.append(f)
        
        # Save final output
        with open(output_pdf, 'wb') as f:
            merger.write(f)
        
        print(f"\nSuccessfully created {output_pdf} with {len(chapter_pdfs)} chapters.")
    except Exception as e:
        print(f"Failed to merge PDFs: {str(e)}")
    finally:
        # Clean up temporary files
        for pdf in chapter_pdfs + [toc_pdf]:
            try:
                os.remove(pdf)
            except OSError:
                pass

def create_pdf_from_html_folder(folder_path, output_pdf):
    """Main function to convert HTML folder to PDF"""
    html_files = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith('.html')],
        key=lambda x: extract_chapter_number(x)
    )
    
    if not html_files:
        print("No HTML files found in the directory.")
        return
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    temp_pdfs = []
    toc_entries = []
    
    for i, html_file in enumerate(html_files):
        html_path = os.path.join(folder_path, html_file)
        chapter_name = extract_chapter_name(html_path, html_file)
        toc_entries.append((i+1, chapter_name, html_file))
        
        # Process content
        clean_html = extract_content_area(html_path)
        if not clean_html:
            print(f"Skipping {html_file} - no content-area found")
            continue
            
        temp_pdf = f"temp_{i}.pdf"
        try:
            pdfkit.from_string(
                clean_html,
                temp_pdf,
                configuration=config,
                options=pdf_options
            )
            temp_pdfs.append(temp_pdf)
            print(f"Processed chapter {i+1}: {chapter_name}")
        except Exception as e:
            print(f"Failed to process {html_file}: {str(e)}")
            continue
    
    if temp_pdfs:
        create_and_merge_toc(toc_entries, temp_pdfs, output_pdf)
    else:
        print("No valid content found to convert.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert HTML files to a single PDF with table of contents.')
    parser.add_argument('folder', help='Path to folder containing HTML files')
    parser.add_argument('output', help='Output PDF file path')
    
    args = parser.parse_args()
    
    # Verify wkhtmltopdf is accessible
    try:
        test_pdf = "test.pdf"
        pdfkit.from_string("<html><body><h1>Test</h1></body></html>", test_pdf, configuration=config)
        os.remove(test_pdf)
    except Exception as e:
        print(f"Error with wkhtmltopdf configuration: {e}")
        print("Please verify the path to wkhtmltopdf is correct.")
        exit(1)
    
    create_pdf_from_html_folder(args.folder, args.output)
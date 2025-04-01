#!/usr/bin/env python3
import os
import pdfkit
import re
from PyPDF2 import PdfMerger
import argparse

def extract_chapter_number(filename):
    """Extract chapter number from filename, handling various formats"""
    basename = os.path.splitext(os.path.basename(filename))[0].lower()
    
    # Try to find numbers in different patterns
    patterns = [
        r'chapter_(\d+)',  # chapter_1
        r'ch(\d+)',        # ch1
        r'(\d+)',          # 1
        r'[^\d]*(\d+)[^\d]*'  # any number in filename
    ]
    
    for pattern in patterns:
        match = re.search(pattern, basename)
        if match:
            return int(match.group(1))
    
    # If no number found, return a large number to sort these last
    return 99999

def html_to_pdf_chapter_packer(input_folder, output_pdf, title="Novel", toc=True, cover_page=None):
    """Convert HTML files to PDF chapters"""
    # Get and sort HTML files
    html_files = [os.path.join(input_folder, f) 
                 for f in os.listdir(input_folder) 
                 if f.lower().endswith('.html')]
    
    html_files.sort(key=extract_chapter_number)
    
    if not html_files:
        print("No HTML files found!")
        return

    # PDF options
    options = {
        'encoding': 'UTF-8',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'footer-center': '[page]',
        'footer-font-size': '10',
        'header-left': title,
        'header-font-size': '10',
        'header-line': True,
    }

    if toc:
        toc_options = {
            'toc-header-text': 'Table of Contents',
            'toc-level-indentation': '2em',
            'toc-text-size-shrink': 0.9,
        }
        options.update(toc_options)
    
    # Temporary directory for individual PDFs
    temp_dir = os.path.join(input_folder, "temp_pdfs")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate individual PDFs
    individual_pdfs = []
    for i, html_file in enumerate(html_files):
        chapter_options = options.copy()
        chapter_title = os.path.splitext(os.path.basename(html_file))[0]
        chapter_options['header-right'] = f"Chapter {i+1}: {chapter_title}"
        
        output_file = os.path.join(temp_dir, f"chapter_{i+1}.pdf")
        pdfkit.from_file(html_file, output_file, options=chapter_options)
        individual_pdfs.append(output_file)
    
    # Merge PDFs
    merger = PdfMerger()
    
    # Add cover page if provided
    if cover_page and os.path.exists(cover_page):
        cover_pdf = os.path.join(temp_dir, "cover.pdf")
        pdfkit.from_file(cover_page, cover_pdf, options={'margin-top': '0', 'margin-right': '0', 
                                                       'margin-bottom': '0', 'margin-left': '0'})
        merger.append(cover_pdf)
    
    # Add TOC if enabled
    if toc:
        toc_html = generate_toc_html(html_files, title)
        toc_pdf = os.path.join(temp_dir, "toc.pdf")
        toc_options = options.copy()
        toc_options['header-right'] = "Table of Contents"
        pdfkit.from_string(toc_html, toc_pdf, options=toc_options)
        merger.append(toc_pdf)
    
    # Add chapters
    for pdf in individual_pdfs:
        merger.append(pdf)
    
    # Write output
    merger.write(output_pdf)
    merger.close()
    
    # Clean up temporary files
    for pdf in individual_pdfs:
        os.remove(pdf)
    if toc and os.path.exists(os.path.join(temp_dir, "toc.pdf")):
        os.remove(os.path.join(temp_dir, "toc.pdf"))
    if cover_page and os.path.exists(os.path.join(temp_dir, "cover.pdf")):
        os.remove(os.path.join(temp_dir, "cover.pdf"))
    os.rmdir(temp_dir)
    
    print(f"Successfully created {output_pdf} with {len(html_files)} chapters.")

def generate_toc_html(html_files, title):
    """Generate HTML for table of contents"""
    toc_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Table of Contents</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            h1 {{ text-align: center; margin-bottom: 2em; }}
            .toc-entry {{ margin-bottom: 0.5em; }}
            .toc-chapter {{ font-weight: bold; }}
            .toc-page {{ float: right; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <h2>Table of Contents</h2>
        <div id="toc">
    """
    
    for i, html_file in enumerate(html_files):
        chapter_title = os.path.splitext(os.path.basename(html_file))[0]
        toc_html += f"""
            <div class="toc-entry">
                <span class="toc-chapter">Chapter {i+1}: {chapter_title}</span>
                <span class="toc-page"></span>
            </div>
        """
    
    toc_html += """
        </div>
    </body>
    </html>
    """
    return toc_html


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input folder with HTML files')
    parser.add_argument('-o', '--output', default='output.pdf', help='Output PDF file')
    parser.add_argument('-t', '--title', default='Novel', help='Document title')
    parser.add_argument('-c', '--cover', help='Cover page HTML')
    parser.add_argument('--no-toc', action='store_false', dest='toc', help='Disable TOC')
    
    args = parser.parse_args()
    
    html_to_pdf_chapter_packer(
        input_folder=os.path.abspath(args.input),
        output_pdf=os.path.abspath(args.output),
        title=args.title,
        toc=args.toc,
        cover_page=args.cover
    )
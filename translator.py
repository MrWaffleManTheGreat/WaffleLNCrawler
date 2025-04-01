import os
import tempfile
import time
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import re
import random

class PDFTranslator:
    def __init__(self, source_lang='auto', target_lang='en'):
        """
        Initialize the PDF translator with source and target languages.
        
        Args:
            source_lang (str): Source language code (e.g., 'auto' for auto-detection)
            target_lang (str): Target language code (e.g., 'en' for English)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def split_pdf(self, pdf_path, output_dir):
        """
        Split a PDF into individual pages.
        
        Args:
            pdf_path (str): Path to the input PDF file
            output_dir (str): Directory to save individual pages
            
        Returns:
            list: List of paths to individual page PDFs
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        reader = PdfReader(pdf_path)
        page_paths = []
        
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            page_path = os.path.join(output_dir, f'page_{i+1}.pdf')
            with open(page_path, 'wb') as f:
                writer.write(f)
                
            page_paths.append(page_path)
            
        return page_paths
    
    def translate_pdf_page(self, pdf_path):
        """
        Translate a single PDF page using Google Translate.
        
        Args:
            pdf_path (str): Path to the PDF page to translate
            
        Returns:
            bytes: Translated PDF content
        """
        # First, get the Google Translate upload page to extract the token
        translate_url = f'https://translate.google.com/?sl={self.source_lang}&tl={self.target_lang}&op=docs'
        response = self.session.get(translate_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the upload token (this might need adjustment if Google changes their HTML)
        token_pattern = re.compile(r'upload-form.+?action="(.+?)"', re.DOTALL)
        match = token_pattern.search(response.text)
        if not match:
            raise Exception("Could not find upload token in Google Translate page")
            
        upload_url = 'https://translate.google.com' + match.group(1)
        
        # Prepare the file upload
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            upload_response = self.session.post(upload_url, files=files)
            
        if upload_response.status_code != 200:
            raise Exception(f"Upload failed with status code {upload_response.status_code}")
            
        # Parse the response to get the download URL
        soup = BeautifulSoup(upload_response.text, 'html.parser')
        download_link = soup.find('a', {'class': 'download-button'})
        if not download_link:
            raise Exception("Could not find download link in response")
            
        download_url = 'https://translate.google.com' + download_link['href']
        
        # Download the translated PDF
        time.sleep(random.uniform(2, 5))  # Add delay before downloading
        download_response = self.session.get(download_url)
        
        if download_response.status_code != 200:
            raise Exception(f"Download failed with status code {download_response.status_code}")
            
        return download_response.content
    
    def merge_pdfs(self, pdf_contents, output_path):
        """
        Merge multiple PDF contents into a single PDF.
        
        Args:
            pdf_contents (list): List of PDF content bytes
            output_path (str): Path to save the merged PDF
        """
        writer = PdfWriter()
        
        for content in pdf_contents:
            reader = PdfReader(BytesIO(content))
            for page in reader.pages:
                writer.add_page(page)
                
        with open(output_path, 'wb') as f:
            writer.write(f)
    
    def translate_pdf(self, input_pdf, output_pdf):
        """
        Translate a complete PDF file.
        
        Args:
            input_pdf (str): Path to the input PDF file
            output_pdf (str): Path to save the translated PDF
        """
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            print("Splitting PDF into individual pages...")
            page_paths = self.split_pdf(input_pdf, temp_dir)
            
            translated_contents = []
            
            print(f"Translating {len(page_paths)} pages...")
            for i, page_path in enumerate(page_paths):
                print(f"Translating page {i+1}/{len(page_paths)}...")
                try:
                    translated_content = self.translate_pdf_page(page_path)
                    translated_contents.append(translated_content)
                except Exception as e:
                    print(f"Error translating page {i+1}: {str(e)}")
                    # If translation fails, add the original page
                    with open(page_path, 'rb') as f:
                        translated_contents.append(f.read())
                
            print("Merging translated pages...")
            self.merge_pdfs(translated_contents, output_pdf)
            
        print(f"Translation complete. Saved to {output_pdf}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate PDF files using Google Translate')
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('output_pdf', help='Path to save the translated PDF')
    parser.add_argument('--source', default='auto', help='Source language code (default: auto)')
    parser.add_argument('--target', default='en', help='Target language code (default: en)')
    
    args = parser.parse_args()
    
    translator = PDFTranslator(source_lang=args.source, target_lang=args.target)
    translator.translate_pdf(args.input_pdf, args.output_pdf)

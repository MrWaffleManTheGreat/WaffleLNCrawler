import os
import time
import requests
from bs4 import BeautifulSoup
import html

# Configuration
base_url = "https://www.fortuneeternal.com/novel/the-artist-who-paints-dungeon-raw-novel/chapter-"
start_chapter = 1
end_chapter = 357  # Test with smaller range first
output_dir = "english_novel"
delay = 3  # More generous delay to allow translation

# Create output directory
os.makedirs(output_dir, exist_ok=True)
print(f"Saving files to: {os.path.abspath(output_dir)}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def activate_english_translation(session, url):
    """Force English translation through the widget"""
    # First get the page to set cookies
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the translation widget
    translation_div = soup.find('div', class_='gtranslate_wrapper')
    if translation_div:
        # Extract the English translation link
        english_link = translation_div.find('a', title='English')
        if english_link:
            # Get the data-gt-lang value for English
            lang_code = english_link.get('data-gt-lang', 'en')
            
            # Set the googtrans cookie to force English
            session.cookies.set('googtrans', f'/auto/{lang_code}')
            
            # Make a new request with the translation cookie
            return session.get(url, headers=headers)
    
    return response

def save_chapter(chapter, content):
    """Save chapter with proper .html extension"""
    filename = f"chapter-{chapter}.html"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

for chapter in range(start_chapter, end_chapter + 1):
    url = f"{base_url}{chapter}/"
    print(f"\nProcessing chapter {chapter}...")
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # First request to activate English translation
        response = activate_english_translation(session, url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title and content
        title = soup.find('h1').get_text(strip=True)
        content_div = soup.find('div', class_='entry-content')
        
        # Clean up content (keep translation widget visible)
        for element in content_div.find_all(['script', 'style', 'iframe', 'nav']):
            element.decompose()
        
        # Save as HTML with translation widget intact
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    {str(soup.find('div', class_='gtranslate_wrapper'))}
    <h1>{title}</h1>
    {str(content_div)}
</body>
</html>"""
        
        saved_file = save_chapter(chapter, html_content)
        print(f"✓ Saved: {os.path.basename(saved_file)}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    time.sleep(delay)

print("\nDownload complete! All chapters saved with English translations.")
print(f"Location: {os.path.abspath(output_dir)}")
#!/usr/bin/env python3
import os
import glob
from convert_html_to_md import convert_html_to_markdown

def main():
    # Get all HTML files except the one we already converted
    html_files = glob.glob('blog-posts-html/*.html')
    html_files = [f for f in html_files if 'wolfi-arm64.html' not in f]
    
    # Create markdown directory if it doesn't exist
    os.makedirs('blog-posts-markdown', exist_ok=True)
    
    # Convert each file
    for html_file in html_files:
        base_name = os.path.basename(html_file).replace('.html', '.md')
        output_file = os.path.join('blog-posts-markdown', base_name)
        
        try:
            convert_html_to_markdown(html_file, output_file)
        except Exception as e:
            print(f"Error converting {html_file}: {e}")
    
    # Move the already converted file to the markdown directory
    if os.path.exists('wolfi-arm64.md'):
        os.rename('wolfi-arm64.md', 'blog-posts-markdown/wolfi-arm64.md')

if __name__ == "__main__":
    main()
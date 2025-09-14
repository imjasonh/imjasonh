#!/usr/bin/env python3
import os
import re

def update_markdown_images():
    """Update image references in markdown files to use local paths"""
    
    # Read the image mapping
    mappings = {}
    current_file = None
    
    with open('image_mapping.txt', 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if line and not line.startswith(' '):
            current_file = line
            mappings[current_file] = []
        elif line and current_file:
            # Parse the mapping
            parts = line.strip().split(' -> ')
            if len(parts) == 2:
                old_url = parts[0]
                new_path = parts[1]
                # Convert to relative path from markdown directory
                relative_path = os.path.relpath(new_path, 'blog-posts-markdown')
                mappings[current_file].append((old_url, relative_path))
    
    # Update each markdown file
    for md_file, url_mappings in mappings.items():
        if not url_mappings:
            continue
            
        print(f"Updating {os.path.basename(md_file)}...")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace each URL with local path
        for old_url, new_path in url_mappings:
            # Escape special regex characters in URL
            escaped_url = re.escape(old_url)
            # Replace in markdown image syntax
            pattern = f'(!\\[[^\\]]*\\]\\(){escaped_url}(\\))'
            replacement = f'\\1{new_path}\\2'
            content = re.sub(pattern, replacement, content)
            print(f"  ✓ Updated image reference")
        
        # Write back
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("\nAll image references updated!")

if __name__ == "__main__":
    update_markdown_images()
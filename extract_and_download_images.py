#!/usr/bin/env python3
import re
import os
import subprocess
from urllib.parse import unquote
import glob

def extract_images_from_markdown(md_file):
    """Extract image URLs from a markdown file"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all image references
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    matches = re.findall(image_pattern, content)
    
    images = []
    for alt_text, url in matches:
        # Skip if it's already a local path
        if not url.startswith('http'):
            continue
        images.append((alt_text, url))
    
    return images

def get_image_filename(url, post_name, index):
    """Generate a descriptive filename for an image"""
    # Extract file extension
    ext = '.png'
    for extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
        if extension in url.lower():
            ext = extension
            break
    
    # Create descriptive name
    clean_post_name = post_name.replace('-', '_')
    return f"{clean_post_name}_img{index}{ext}"

def download_image(url, output_path):
    """Download an image using curl"""
    cmd = ['curl', '-s', url, '-o', output_path]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def main():
    # Get all markdown files
    md_files = glob.glob('blog-posts-markdown/*.md')
    
    # Track all images to download
    all_images = {}
    
    for md_file in md_files:
        post_name = os.path.basename(md_file).replace('.md', '')
        images = extract_images_from_markdown(md_file)
        
        if images:
            all_images[md_file] = images
            print(f"\n{post_name}: {len(images)} images found")
            for i, (alt, url) in enumerate(images):
                print(f"  {i+1}. {alt[:50]}... -> {url[:80]}...")
    
    # Download images
    print("\n\nDownloading images...")
    image_mapping = {}
    
    for md_file, images in all_images.items():
        post_name = os.path.basename(md_file).replace('.md', '')
        image_mapping[md_file] = []
        
        for i, (alt_text, url) in enumerate(images):
            filename = get_image_filename(url, post_name, i + 1)
            output_path = os.path.join('blog-images', filename)
            
            print(f"Downloading {post_name} image {i+1}...")
            if download_image(url, output_path):
                image_mapping[md_file].append((url, output_path))
                print(f"  ✓ Saved as {filename}")
            else:
                print(f"  ✗ Failed to download")
    
    # Save mapping for updating markdown files
    with open('image_mapping.txt', 'w') as f:
        for md_file, mappings in image_mapping.items():
            f.write(f"{md_file}\n")
            for old_url, new_path in mappings:
                f.write(f"  {old_url} -> {new_path}\n")
            f.write("\n")

if __name__ == "__main__":
    main()
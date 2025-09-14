#!/usr/bin/env python3
import re
from html.parser import HTMLParser
from urllib.parse import unquote
import html

class HTMLToMarkdownConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown = []
        self.current_tag = []
        self.link_href = None
        self.in_content = False
        self.content_depth = 0
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'svg', 'button'}
        self.in_skip = False
        self.skip_depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Skip certain tags
        if tag in self.skip_tags:
            self.in_skip = True
            self.skip_depth = 1
            return
            
        if self.in_skip:
            self.skip_depth += 1
            return
            
        # Check if we're in the main content area
        if tag == 'div' and 'class' in attrs_dict and 'richtext' in attrs_dict['class']:
            self.in_content = True
            self.content_depth = 1
            return
            
        if self.in_content:
            if tag in ['div', 'section', 'article']:
                self.content_depth += 1
                
        if not self.in_content:
            return
            
        self.current_tag.append(tag)
        
        if tag == 'h1':
            self.markdown.append('\n# ')
        elif tag == 'h2':
            self.markdown.append('\n## ')
        elif tag == 'h3':
            self.markdown.append('\n### ')
        elif tag == 'h4':
            self.markdown.append('\n#### ')
        elif tag == 'h5':
            self.markdown.append('\n##### ')
        elif tag == 'h6':
            self.markdown.append('\n###### ')
        elif tag == 'p':
            self.markdown.append('\n\n')
        elif tag == 'br':
            self.markdown.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.markdown.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown.append('*')
        elif tag == 'code':
            self.markdown.append('`')
        elif tag == 'pre':
            self.markdown.append('\n```\n')
        elif tag == 'ul':
            self.markdown.append('\n')
        elif tag == 'ol':
            self.markdown.append('\n')
        elif tag == 'li':
            self.markdown.append('\n- ')
        elif tag == 'a':
            self.link_href = attrs_dict.get('href', '')
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', 'Image')
            
            # Try srcSet first for higher quality image
            srcset = attrs_dict.get('srcset', '')
            if srcset:
                # Get the highest resolution image from srcSet
                srcset_parts = srcset.split(',')
                if srcset_parts:
                    # Take the last one (usually highest resolution)
                    src = srcset_parts[-1].strip().split(' ')[0]
            
            # Handle Next.js image URLs
            if src.startswith('/_next/image?url='):
                # Extract the actual image URL
                match = re.search(r'url=([^&]+)', src)
                if match:
                    src = unquote(match.group(1))
            
            self.markdown.append(f'\n\n![{alt}]({src})\n\n')
            
    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.in_skip:
            self.skip_depth -= 1
            if self.skip_depth == 0:
                self.in_skip = False
            return
            
        if self.in_skip:
            self.skip_depth -= 1
            return
            
        if self.in_content:
            if tag in ['div', 'section', 'article']:
                self.content_depth -= 1
                if self.content_depth == 0:
                    self.in_content = False
                    
        if not self.in_content or not self.current_tag:
            return
            
        if self.current_tag and self.current_tag[-1] == tag:
            self.current_tag.pop()
            
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.markdown.append('\n')
        elif tag == 'p':
            self.markdown.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.markdown.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown.append('*')
        elif tag == 'code':
            self.markdown.append('`')
        elif tag == 'pre':
            self.markdown.append('\n```\n')
        elif tag == 'a' and self.link_href:
            self.markdown.append(f']({self.link_href})')
            self.link_href = None
            
    def handle_data(self, data):
        if self.in_skip or not self.in_content:
            return
            
        if self.current_tag and self.current_tag[-1] == 'a' and self.link_href:
            self.markdown.append('[' + html.unescape(data.strip()))
        else:
            self.markdown.append(html.unescape(data.strip()))
            
    def get_markdown(self):
        # Clean up the markdown
        result = ''.join(self.markdown)
        # Remove excessive whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)
        # Clean up spaces
        result = re.sub(r' +', ' ', result)
        # Remove zero-width characters
        result = result.replace('\u200d', '')
        result = result.replace('\u200b', '')
        result = result.replace('\ufeff', '')
        # Fix link spacing
        result = re.sub(r'\]\s*\(', '](', result)
        result = re.sub(r'([a-zA-Z0-9])\[', r'\1 [', result)
        return result.strip()

def convert_html_to_markdown(html_file, output_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # Extract title
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
    title = title_match.group(1) if title_match else 'Untitled'
    
    # Extract author and date
    author_match = re.search(r'<span[^>]*>([^<]+), [^<]+</span>', html_content)
    author = author_match.group(1) if author_match else ''
    
    date_match = re.search(r'<time>([^<]+)</time>', html_content)
    date = date_match.group(1) if date_match else ''
    
    converter = HTMLToMarkdownConverter()
    converter.feed(html_content)
    
    markdown = f"# {title}\n\n"
    if author:
        markdown += f"*{author}*\n\n"
    if date:
        markdown += f"*{date}*\n\n"
    
    markdown += converter.get_markdown()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Converted {html_file} to {output_file}")

if __name__ == "__main__":
    convert_html_to_markdown('blog-posts-html/wolfi-arm64.html', 'wolfi-arm64.md')
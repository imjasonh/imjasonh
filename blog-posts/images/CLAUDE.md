# HTML to Markdown Conversion Process

This document summarizes the steps taken to convert HTML blog posts to Markdown while preserving all content and images.

## Steps Taken

### 1. Initial HTML Analysis
- Fetched raw HTML content of all blog posts listed in README.md using curl
- Stored HTML files in `blog-posts-html/` directory
- Created `images.txt` listing all images found across the blog posts

### 2. Image Extraction and Download
- Identified 4 unique images in wolfi-arm64.html:
  - `arm64_1.png` - Main article diagram
  - `This_Shit_Is_Hard__Hardening_glibc.png` - Sidebar/related article image
  - `13__Kernel-Independent_FIPS_for_Java.png` - Sidebar/related article image
  - `21__Resiliency_by_Design_and_the_Importance_of_Internal_Developer_Platforms.png` - Sidebar/related article image
- Downloaded all images using curl to `blog-images/` directory
- Renamed images with descriptive names (e.g., `wolfi-arm64-diagram.png`)

### 3. HTML to Markdown Converter Development
Created `convert_html_to_md.py` with the following features:
- Custom HTMLParser to extract main content from `<div class="richtext">` sections
- Preserves all text without summarization
- Converts HTML elements to Markdown equivalents:
  - Headers (h1-h6) → Markdown headers (#, ##, etc.)
  - Links `<a>` → `[text](url)`
  - Images `<img>` → `![alt](src)`
  - Emphasis `<em>`, `<i>` → `*text*`
  - Strong `<strong>`, `<b>` → `**text**`
- Handles Next.js image URLs by extracting the actual image URL from query parameters
- Removes zero-width characters and fixes spacing issues

### 4. Conversion Process
- Ran the converter on wolfi-arm64.html as a test
- Successfully converted all content including:
  - Title, author, and date
  - All article text with proper paragraph spacing
  - All hyperlinks preserved
  - Main content image included
- Updated image reference to point to local file: `blog-images/wolfi-arm64-diagram.png`

### 5. Quality Verification
- Verified all text content was preserved without loss
- Confirmed proper Markdown formatting
- Checked that the main article image was correctly embedded
- Noted that the other 3 images were sidebar/navigation elements, not part of the main article content

## Key Technical Details

- Used `srcset` attribute when available to get highest resolution images
- Handled URL-encoded image paths in Next.js `/_next/image` URLs
- Skipped navigation, header, footer, and other non-content elements
- Maintained heading hierarchy and link formatting
- Cleaned up HTML entities and special characters

## Result

Successfully converted wolfi-arm64.html to a clean Markdown file with:
- Complete text content preserved
- Proper formatting and structure
- Embedded image with local reference
- All links maintained
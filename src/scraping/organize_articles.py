import os
import re
from pathlib import Path
from collections import defaultdict

def organize_articles_by_postfix():
    """
    Organize articles by unique text postfix into numbered folders.
    File structure: page{number}_{text}_{id}.txt
    Extract {text} and create folders numbered 1, 2, 3, etc.
    """
    
    scraped_articles_dir = Path(__file__).parent / "scraped_articles"
    
    if not scraped_articles_dir.exists():
        print(f"Directory not found: {scraped_articles_dir}")
        return
    
    # Pattern to match: page{number}_{text}_{id}.txt
    # Groups: (page number, text, id)
    pattern = r'page(\d+)_(.+)_(\d+)\.txt$'
    
    # Dictionary to store unique texts and their files
    text_files_map = defaultdict(list)
    
    # First pass: collect all unique texts and their files
    all_files = list(scraped_articles_dir.glob("*.txt"))
    print(f"Found {len(all_files)} files")
    
    for file_path in all_files:
        filename = file_path.name
        match = re.match(pattern, filename)
        
        if match:
            page_num, text, file_id = match.groups()
            text_files_map[text].append(file_path)
        else:
            print(f"Warning: File '{filename}' doesn't match expected pattern")
    
    print(f"Found {len(text_files_map)} unique texts")
    
    # Create folders with incremental numbers
    unique_texts = sorted(text_files_map.keys())
    
    for folder_num, unique_text in enumerate(unique_texts, start=1):
        folder_path = Path(__file__).parent.parent / "assets" / "files" / str(folder_num)
        
        # Create folder
        folder_path.mkdir(exist_ok=True)
        
        # Move files to this folder
        files = text_files_map[unique_text]
        print(f"\nFolder {folder_num}: '{unique_text}' ({len(files)} files)")
        
        for file_path in files:
            dest_path = folder_path / file_path.name
            file_path.rename(dest_path)
            print(f"  Moved: {file_path.name}")
    
    print("\n✓ Organization complete!")
    print(f"Created {len(unique_texts)} folders with {len(all_files)} files")

if __name__ == "__main__":
    organize_articles_by_postfix()

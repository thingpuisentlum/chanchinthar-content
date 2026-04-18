import os
import json
from datetime import datetime

CONTENT_DIR = 'content'
PUBLIC_DIR = 'public'
FEEDS_DIR = os.path.join(PUBLIC_DIR, 'feeds')
CATEGORY_FEEDS_DIR = os.path.join(FEEDS_DIR, 'category')
PAGE_SIZE = 15

def parse_simple_yaml(yaml_str):
    """Simple YAML parser for basic key-value pairs and lists."""
    data = {}
    for line in yaml_str.splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        
        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            data[key] = [item.strip().strip('"').strip("'") for item in items]
        else:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                data[key] = value[1:-1]
            else:
                data[key] = value
    return data

def parse_article(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content.startswith('---'):
            return None
        
        parts = content.split('---')
        if len(parts) < 3:
            return None
            
        metadata = parse_simple_yaml(parts[1])
        metadata['contentPath'] = os.path.relpath(file_path, 'content').replace('\\', '/')
        metadata['contentPath'] = 'articles/' + metadata['contentPath']
        return metadata

def build():
    all_posts = []
    
    # 1. Collect all articles
    for root, dirs, files in os.walk(CONTENT_DIR):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                post = parse_article(full_path)
                if post:
                    all_posts.append(post)
                    dest_path = os.path.join(PUBLIC_DIR, post['contentPath'])
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(full_path, 'r', encoding='utf-8') as f_in, open(dest_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(f_in.read())

    all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)

    # 2. Generate Latest Feed
    os.makedirs(FEEDS_DIR, exist_ok=True)
    with open(os.path.join(FEEDS_DIR, 'latest.json'), 'w', encoding='utf-8') as f:
        json.dump(all_posts[:PAGE_SIZE * 2], f, indent=2)

    # 3. Generate Trending Feed
    trending = [p for p in all_posts if 'Trending' in p.get('tags', [])]
    with open(os.path.join(FEEDS_DIR, 'trending.json'), 'w', encoding='utf-8') as f:
        json.dump(trending[:10], f, indent=2)

    # 4. Generate Categorized and Nested Category Feeds
    os.makedirs(CATEGORY_FEEDS_DIR, exist_ok=True)
    categories = set(p['category'] for p in all_posts if 'category' in p)
    for cat in categories:
        cat_posts = [p for p in all_posts if p.get('category') == cat]
        cat_slug = cat.lower().replace(' ', '_')
        cat_dir = os.path.join(CATEGORY_FEEDS_DIR, cat_slug)
        os.makedirs(cat_dir, exist_ok=True)
        
        # Paginate
        total_pages = (len(cat_posts) + PAGE_SIZE - 1) // PAGE_SIZE
        for i in range(0, len(cat_posts), PAGE_SIZE):
            page_num = (i // PAGE_SIZE) + 1
            page_data = cat_posts[i:i + PAGE_SIZE]
            
            with open(os.path.join(cat_dir, f'{page_num}.json'), 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2)
        
        with open(os.path.join(cat_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({"total_pages": total_pages}, f)

    print(f"Successfully built nested feeds for {len(all_posts)} articles.")

if __name__ == '__main__':
    build()

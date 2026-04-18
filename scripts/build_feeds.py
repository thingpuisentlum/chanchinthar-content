import os
import json
import re
from datetime import datetime

CONTENT_DIR = 'content'
PUBLIC_DIR = 'public'
FEEDS_DIR = os.path.join(PUBLIC_DIR, 'feeds')
CATEGORY_FEEDS_DIR = os.path.join(FEEDS_DIR, 'category')
PAGE_SIZE = 15

def parse_simple_yaml(yaml_str):
    data = {}
    for line in yaml_str.splitlines():
        if ':' not in line: continue
        key, value = line.split(':', 1)
        key, value = key.strip(), value.strip()
        if value.startswith('[') and value.endswith(']'):
            data[key] = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',')]
        else:
            data[key] = value.strip('"').strip("'")
    return data

def parse_article(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()
        
    # Use regex to find frontmatter at the start of the file
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', raw_content, re.DOTALL)
    if not match:
        return None, None
        
    metadata = parse_simple_yaml(match.group(1))
    article_body = match.group(2).strip()
    
    metadata['contentPath'] = os.path.relpath(file_path, 'content').replace('\\', '/')
    metadata['contentPath'] = 'articles/' + metadata['contentPath']
    # Ensure content field is empty in JSON to avoid frontend confusion
    metadata['content'] = "" 
    return metadata, article_body

def build():
    all_posts = []
    for root, dirs, files in os.walk(CONTENT_DIR):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                post, body = parse_article(full_path)
                if post:
                    all_posts.append(post)
                    dest_path = os.path.join(PUBLIC_DIR, post['contentPath'])
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(body)

    all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
    os.makedirs(FEEDS_DIR, exist_ok=True)
    
    with open(os.path.join(FEEDS_DIR, 'latest.json'), 'w', encoding='utf-8') as f:
        json.dump(all_posts[:PAGE_SIZE * 2], f, indent=2)

    trending = [p for p in all_posts if 'Trending' in p.get('tags', [])]
    with open(os.path.join(FEEDS_DIR, 'trending.json'), 'w', encoding='utf-8') as f:
        json.dump(trending[:10], f, indent=2)

    categories = set(p['category'] for p in all_posts if 'category' in p)
    for cat in categories:
        cat_posts = [p for p in all_posts if p.get('category') == cat]
        cat_slug = cat.lower().replace(' ', '_')
        cat_dir = os.path.join(CATEGORY_FEEDS_DIR, cat_slug)
        os.makedirs(cat_dir, exist_ok=True)
        total_pages = (len(cat_posts) + PAGE_SIZE - 1) // PAGE_SIZE
        for i in range(0, len(cat_posts), PAGE_SIZE):
            page_num = (i // PAGE_SIZE) + 1
            json.dump(cat_posts[i:i + PAGE_SIZE], open(os.path.join(cat_dir, f'{page_num}.json'), 'w', encoding='utf-8'), indent=2)
        json.dump({"total_pages": total_pages}, open(os.path.join(cat_dir, 'meta.json'), 'w', encoding='utf-8'))

    print(f"Successfully built feeds for {len(all_posts)} articles (Final Strip).")

if __name__ == '__main__':
    build()

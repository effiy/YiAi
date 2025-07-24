import os
import json
import argparse

ext_map = {
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.json': 'json',
    '.css': 'css',
    '.html': 'html',
    '.md': 'markdown',
    '.svg': 'svg',
    '.env': 'env',
    '.txt': 'text',
}
binary_exts = {'.jpg', '.jpeg', '.png', '.ico', '.gif', '.bmp', '.webp', '.ttf', '.otf', '.woff', '.woff2'}

def get_language(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in binary_exts:
        return 'binary'
    return ext_map.get(ext, 'text')

def get_content(filepath, language):
    if language == 'binary':
        return '(图片二进制内容省略)'
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return '(无法读取内容)'

def should_include(file, include_exts, exclude_exts, include_names, exclude_names):
    ext = os.path.splitext(file)[1].lower()
    if include_exts and ext not in include_exts:
        return False
    if exclude_exts and ext in exclude_exts:
        return False
    if include_names and file not in include_names:
        return False
    if exclude_names and file in exclude_names:
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='生成 files.json 格式的文件列表')
    parser.add_argument('--dir', type=str, default='.', help='要遍历的目录（默认当前目录）')
    parser.add_argument('--output', type=str, default='files.json', help='输出文件路径')
    parser.add_argument('--include-ext', type=str, nargs='*', help='只包含这些扩展名（如 .js .json）')
    parser.add_argument('--exclude-ext', type=str, nargs='*', help='排除这些扩展名')
    parser.add_argument('--include-name', type=str, nargs='*', help='只包含这些文件名')
    parser.add_argument('--exclude-name', type=str, nargs='*', help='排除这些文件名')
    args = parser.parse_args()

    result = []
    import os

    root_dir_name = os.path.basename(args.dir.rstrip('/'))

    for root, dirs, files in os.walk(args.dir):
        for file in files:
            if file.startswith('.'):
                continue
            if not should_include(
                file,
                set(args.include_ext) if args.include_ext else None,
                set(args.exclude_ext) if args.exclude_ext else None,
                set(args.include_name) if args.include_name else None,
                set(args.exclude_name) if args.exclude_name else None
            ):
                continue
            # 以 args.dir 为根生成相对路径
            rel_path = os.path.relpath(os.path.join(root, file), args.dir)
            rel_path = rel_path.replace('\\', '/')
            file_id = f"{root_dir_name}/{rel_path}"
            language = get_language(file)
            content = get_content(os.path.join(root, file), language)
            size = os.path.getsize(os.path.join(root, file))
            ext = os.path.splitext(file)[1].lower()
            if ext.startswith('.'):
                ext = ext[1:]
            result.append({
                "fileId": file_id,
                "language": language,
                "content": content,
                "size": size,
                "ext": ext
            })

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'已生成 {args.output}')

if __name__ == '__main__':
    main()

import os
import json
import argparse
from datetime import datetime

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

def should_skip_directory(dirname):
    """检查是否应该跳过指定目录"""
    skip_dirs = {'node_modules', '.git', '.svn', '.hg', '__pycache__', '.DS_Store'}
    return dirname in skip_dirs

def build_tree(root, rel_path="", root_dir_name=None, include_ext=None, exclude_dirs=None):
    """
    构建目录树，id字段与files.json中的fileId保持一致
    root_dir_name: 根目录名，所有id都以此为前缀
    rel_path: 相对于根目录的路径
    """
    items = []
    if root_dir_name is None:
        root_dir_name = os.path.basename(os.path.abspath(root))
    for name in sorted(os.listdir(root)):
        if name.startswith('.'):
            continue
        abs_path = os.path.join(root, name)
        # 计算相对路径
        if rel_path == "":
            id_path = f"{root_dir_name}/{name}"
            next_rel_path = name
        else:
            id_path = f"{root_dir_name}/{rel_path}/{name}"
            next_rel_path = f"{rel_path}/{name}"
        id_path = id_path.replace('\\', '/')
        # 过滤目录
        if os.path.isdir(abs_path):
            if should_skip_directory(name):
                continue
            if exclude_dirs and name in exclude_dirs:
                continue
            children = build_tree(abs_path, next_rel_path, root_dir_name, include_ext, exclude_dirs)
            items.append({
                "id": id_path,
                "name": name,
                "type": "folder",
                "children": children
            })
        else:
            # 过滤文件类型
            if include_ext:
                if not any(name.endswith(ext) for ext in include_ext):
                    continue
            items.append({
                "id": id_path,
                "name": name,
                "type": "file"
            })
    return items

def generate_files_json(args):
    """生成 files.json 格式的文件列表"""
    result = []
    # 修正：获取 --dir 参数中的最后一个目录名作为根目录名
    root_dir_name = os.path.basename(os.path.normpath(args.dir))

    for root, dirs, files in os.walk(args.dir):
        # 过滤掉不需要的目录
        dirs[:] = [d for d in dirs if not should_skip_directory(d)]
        
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
            # 以当前目录名为根生成相对路径
            rel_path = os.path.relpath(os.path.join(root, file), args.dir)
            rel_path = rel_path.replace('\\', '/')
            file_id = f"{root_dir_name}/{rel_path}"
            file_id = file_id.replace('\\', '/')
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

def generate_tree_json(args):
    """生成目录树 JSON 文件"""
    # 修正：获取 --root 参数中的最后一个目录名作为根目录名
    root_dir_name = os.path.basename(os.path.normpath(args.root))
    tree = build_tree(
        args.root,
        rel_path="",
        root_dir_name=root_dir_name,
        include_ext=args.include,
        exclude_dirs=args.exclude
    )
    # 外层包一层根目录
    tree_json = {
        "id": root_dir_name,
        "name": root_dir_name,
        "type": "folder",
        "children": tree
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, ensure_ascii=False, indent=2)
    print(f"已生成 {args.output}")

def main():
    parser = argparse.ArgumentParser(description='生成文件列表或目录树 JSON 文件')
    parser.add_argument('--mode', type=str, choices=['files', 'tree', 'default'], required=False,
                       help='生成模式: files(生成files.json格式) 或 tree(生成目录树格式) 或 default(自动生成并输出到当前目录/日期目录下)')
    
    # 通用参数
    parser.add_argument('--output', type=str, required=False, help='输出文件路径')
    parser.add_argument('--path', type=str, default='.', help='要遍历的目录（通用参数，默认当前目录）')
    
    # files 模式参数
    parser.add_argument('--dir', type=str, default='.', help='要遍历的目录（files模式，默认当前目录）')
    parser.add_argument('--include-ext', type=str, nargs='*', help='只包含这些扩展名（files模式，如 .js .json）')
    parser.add_argument('--exclude-ext', type=str, nargs='*', help='排除这些扩展名（files模式）')
    parser.add_argument('--include-name', type=str, nargs='*', help='只包含这些文件名（files模式）')
    parser.add_argument('--exclude-name', type=str, nargs='*', help='排除这些文件名（files模式）')
    
    # tree 模式参数
    parser.add_argument('--root', type=str, help='要遍历的根目录（tree模式）')
    parser.add_argument('--include', type=str, nargs='*', help='只包含指定后缀的文件（tree模式，例如 .js .json）')
    parser.add_argument('--exclude', type=str, nargs='*', help='跳过指定文件夹（tree模式，例如 node_modules .git）')
    
    args = parser.parse_args()

    # 获取输入路径的当前目录名和日期
    # 优先使用 --path 参数（即 args.path），否则为 '.'
    input_path = args.path if hasattr(args, 'path') and args.path else '.'
    # 修正：default 模式下，输出目录名应为 --dir 或 --path 的最后一个目录名
    # 优先使用 --dir，否则用 --path
    if hasattr(args, 'dir') and args.dir:
        input_dir_name = os.path.basename(os.path.normpath(args.dir))
    else:
        input_dir_name = os.path.basename(os.path.normpath(input_path))
    today_str = datetime.now().strftime('%Y-%m-%d')
    default_output_dir = os.path.join(input_dir_name, today_str)

    if args.mode == 'files':
        if not args.output:
            print("请指定 --output 参数")
            return
        # 如果未指定 --dir，则使用通用参数 --path
        if not hasattr(args, 'dir') or args.dir is None:
            args.dir = args.path
        generate_files_json(args)
    elif args.mode == 'tree':
        if not args.root:
            # 如果未指定 --root，则使用通用参数 --path
            if hasattr(args, 'path') and args.path:
                args.root = args.path
            else:
                parser.error("tree模式需要指定 --root 参数")
        if not args.output:
            print("请指定 --output 参数")
            return
        generate_tree_json(args)
    elif args.mode == 'default' or args.mode is None:
        # 创建输出目录（使用 --dir 或 --path 的最后一个目录名）
        if not os.path.exists(default_output_dir):
            os.makedirs(default_output_dir)
        # 生成 files.json
        files_args = argparse.Namespace(
            dir=args.dir if hasattr(args, 'dir') and args.dir else (args.path if hasattr(args, 'path') and args.path else '.'),
            include_ext=None,
            exclude_ext=None,
            include_name=None,
            exclude_name=None,
            output=os.path.join(default_output_dir, 'files.json')
        )
        print(f"正在生成 {files_args.output} ...")
        generate_files_json(files_args)
        # 生成 tree.json
        tree_args = argparse.Namespace(
            root=args.dir if hasattr(args, 'dir') and args.dir else (args.path if hasattr(args, 'path') and args.path else '.'),
            include=None,
            exclude=None,
            output=os.path.join(default_output_dir, 'tree.json')
        )
        print(f"正在生成 {tree_args.output} ...")
        generate_tree_json(tree_args)
        print(f"已全部生成到 {default_output_dir}/")
    else:
        parser.error("未知的 mode 参数")

if __name__ == '__main__':
    main() 

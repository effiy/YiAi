import os
import json
import argparse

def build_tree(root, rel_path="", include_ext=None, exclude_dirs=None):
    items = []
    for name in sorted(os.listdir(root)):
        if name.startswith('.'):
            continue
        abs_path = os.path.join(root, name)
        id_path = os.path.join(rel_path, name) if rel_path else name
        # 过滤目录
        if os.path.isdir(abs_path):
            if exclude_dirs and name in exclude_dirs:
                continue
            children = build_tree(abs_path, id_path, include_ext, exclude_dirs)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成目录树 JSON 文件")
    parser.add_argument('--root', type=str, required=True, help='要遍历的根目录')
    parser.add_argument('--output', type=str, required=True, help='输出文件路径')
    parser.add_argument('--include', type=str, nargs='*', help='只包含指定后缀的文件，例如 .js .json')
    parser.add_argument('--exclude', type=str, nargs='*', help='跳过指定文件夹，例如 node_modules .git')
    args = parser.parse_args()

    tree = build_tree(
        args.root,
        rel_path=os.path.basename(args.root.rstrip('/')),
        include_ext=args.include,
        exclude_dirs=args.exclude
    )
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"已生成 {args.output}")

import os
import json
import argparse
from datetime import datetime
try:
    import requests
except ImportError:
    requests = None

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

# 需要全局跳过的目录名（任意层级命中即跳过）
SKIP_DIRS = {
    'node_modules', '.git', '.svn', '.hg', '__pycache__', '.DS_Store'
}

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

def should_skip_directory(name_or_path):
    """检查是否应该跳过指定目录或路径中包含的目录名"""
    if not name_or_path:
        return False
    norm = os.path.normpath(name_or_path).replace('\\', '/')
    parts = [p for p in norm.split('/') if p]
    return any(part in SKIP_DIRS for part in parts)

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
            if should_skip_directory(abs_path):
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

def build_files_data(path, include, exclude):
    """根据路径与过滤条件构建 files.json 数据列表"""
    result = []
    root_dir_name = os.path.basename(os.path.normpath(path))
    for root, dirs, files in os.walk(path):
        exclude_names = set(exclude) if exclude else set()
        dirs[:] = [d for d in dirs if not should_skip_directory(os.path.join(root, d)) and d not in exclude_names]
        for file in files:
            if file.startswith('.'):  # 隐藏文件
                continue
            if not should_include(
                file,
                set(include) if include else None,
                None,
                None,
                None
            ):
                continue
            rel_path = os.path.relpath(os.path.join(root, file), path).replace('\\', '/')
            file_id = f"{root_dir_name}/{rel_path}".replace('\\', '/')
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
    return result

def generate_files_json(args):
    """生成 files.json 文件"""
    result = build_files_data(args.path, args.include, args.exclude)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'已生成 {args.output}')

def build_tree_data(path, include, exclude):
    """根据路径与过滤条件构建 tree.json 数据结构"""
    root_dir_name = os.path.basename(os.path.normpath(path))
    tree = build_tree(
        path,
        rel_path="",
        root_dir_name=root_dir_name,
        include_ext=include,
        exclude_dirs=exclude
    )
    return {
        "id": root_dir_name,
        "name": root_dir_name,
        "type": "folder",
        "children": tree
    }

def generate_tree_json(args):
    """生成 tree.json 文件"""
    tree_json = build_tree_data(args.path, args.include, args.exclude)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, ensure_ascii=False, indent=2)
    print(f"已生成 {args.output}")

def http_post_json(url, payload, headers=None, timeout=15):
    """发送 JSON POST 请求。优先使用 requests；若缺失则回退至标准库。返回 (status_code, response_text)。"""
    final_headers = {"Content-Type": "application/json"}
    if headers:
        final_headers.update(headers)
    if requests is not None:
        r = requests.post(url, headers=final_headers, data=json.dumps(payload), timeout=timeout)
        return r.status_code, r.text
    else:
        try:
            import urllib.request
            import urllib.error
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=final_headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8", errors="ignore")
                return status, body
        except Exception as e:
            raise e

def http_get_json(url, params=None, headers=None, timeout=15):
    """发送 GET 请求并解析 JSON。优先使用 requests；若缺失则回退至标准库。返回 (status_code, json_obj或None, text)。"""
    final_headers = {}
    if headers:
        final_headers.update(headers)
    if requests is not None:
        r = requests.get(url, headers=final_headers, params=params or {}, timeout=timeout)
        try:
            return r.status_code, r.json(), r.text
        except Exception:
            return r.status_code, None, r.text
    else:
        try:
            import urllib.request
            import urllib.parse
            from urllib.error import URLError, HTTPError
            qs = urllib.parse.urlencode(params or {})
            full_url = url + (('?' in url) and ('&' + qs) or ('?' + qs)) if qs else url
            req = urllib.request.Request(full_url, headers=final_headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8", errors="ignore")
                try:
                    return status, json.loads(body), body
                except Exception:
                    return status, None, body
        except Exception as e:
            raise e

def post_api_mode(args):
    """api 模式：生成数据并存储到远端接口"""
    project_id = os.path.basename(os.path.abspath(args.path if args.path else '.'))
    version_id = args.version_id if hasattr(args, 'version_id') and args.version_id else datetime.now().strftime('%Y-%m-%d')
    # 在上传前先查询是否已存在相同 projectId + versionId 的数据，若存在则跳过上传
    files_url = "https://api.effiy.cn/mongodb/?cname=projectVersionFiles"
    tree_url = "https://api.effiy.cn/mongodb/?cname=projectVersionTree"

    # 参考服务端校验逻辑，附带认证请求头
    headers = {"Content-Type": "application/json"}
    env_token = os.getenv("API_X_TOKEN", "")
    env_user = os.getenv("API_X_USER", "")
    if env_token:
        headers["X-Token"] = env_token
    if env_user:
        headers["X-User"] = env_user

    query_params = {
        "projectId": project_id,
        "versionId": version_id,
        "pageSize": 1,
        "pageNum": 1
    }
    try:
        status_f, data_f, _ = http_get_json(files_url, params=query_params, headers=headers, timeout=15)
        status_t, data_t, _ = http_get_json(tree_url, params=query_params, headers=headers, timeout=15)
        exists_f = (status_f == 200) and isinstance(data_f, dict) and data_f.get("data", {}).get("total", 0) > 0
        exists_t = (status_t == 200) and isinstance(data_t, dict) and data_t.get("data", {}).get("total", 0) > 0
        if exists_f or exists_t:
            print(f"已存在相同 projectId={project_id} 与 versionId={version_id} 的数据，跳过上传。")
            return
    except Exception as e:
        print(f"查询是否存在既有项目版本数据失败，继续尝试上传：{e}")

    files_data = build_files_data(args.path, args.include, args.exclude)
    tree_data = build_tree_data(args.path, args.include, args.exclude)

    tree_payload = {
        "projectId": project_id,
        "versionId": version_id,
        "data": tree_data
    }

    # 参考服务端校验逻辑，附带认证请求头
    # headers 与 url 已在前面定义

    # files: 一个文件一条请求
    success_count, fail_count = 0, 0
    for item in files_data:
        single_payload = {
            "projectId": project_id,
            "versionId": version_id,
            "data": item
        }
        try:
            status1, _ = http_post_json(files_url, single_payload, headers=headers, timeout=15)
            if 200 <= status1 < 300:
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1
    print(f"files 数据上传完成，成功 {success_count} 条，失败 {fail_count} 条")
    try:
        status2, _ = http_post_json(tree_url, tree_payload, headers=headers, timeout=15)
        if 200 <= status2 < 300:
            print(f"tree 数据上传成功，响应: {status2}")
        else:
            print(f"tree 数据上传失败，状态码: {status2}")
    except Exception as e:
        print(f"tree 数据上传异常: {e}")

def main():
    parser = argparse.ArgumentParser(description='生成文件列表或目录树 JSON 文件')
    parser.add_argument('--mode', type=str, choices=['files', 'tree', 'default', 'api'], required=False,
                       help='生成模式: files(生成files.json格式) 或 tree(生成目录树格式) 或 default(本地输出) 或 api(推送到远端API)')
    
    # 通用参数
    parser.add_argument('--output', type=str, required=False, help='输出文件路径')
    parser.add_argument('--path', type=str, default='.', help='要遍历的目录（通用参数，默认当前目录）')
    parser.add_argument('--include', type=str, nargs='*', help='只包含指定后缀的文件（例如 .js .json）')
    parser.add_argument('--exclude', type=str, nargs='*', help='跳过指定文件夹（例如 node_modules .git）')
    parser.add_argument('--version-id', type=str, required=False, help='default 模式下的子目录名/版本号（不传则默认为当天日期，输出到 当前目录/输入目录名/子目录名）')
    
    args = parser.parse_args()

    # 获取输入路径的当前目录名
    input_path = args.path if hasattr(args, 'path') and args.path else '.'
    input_dir_name = os.path.basename(os.path.normpath(input_path))
    # default 模式下的子目录名：优先使用 --version-id，否则使用当天日期
    version_id_dir_name = args.version_id if hasattr(args, 'version_id') and args.version_id else datetime.now().strftime('%Y-%m-%d')
    default_output_dir = os.path.join(input_dir_name, version_id_dir_name)

    if args.mode == 'files':
        if not args.output:
            print("请指定 --output 参数")
            return
        generate_files_json(args)
    elif args.mode == 'tree':
        if not args.output:
            print("请指定 --output 参数")
            return
        generate_tree_json(args)
    elif args.mode == 'default' or args.mode is None:
        # 创建输出目录（使用 --dir 或 --path 的最后一个目录名）
        if not os.path.exists(default_output_dir):
            os.makedirs(default_output_dir)
        # 生成 files.json（沿用 include/exclude）
        files_args = argparse.Namespace(
            path=args.path if hasattr(args, 'path') and args.path else '.',
            include=args.include if hasattr(args, 'include') else None,
            exclude=args.exclude if hasattr(args, 'exclude') else None,
            output=os.path.join(default_output_dir, 'files.json')
        )
        print(f"正在生成 {files_args.output} ...")
        generate_files_json(files_args)
        # 生成 tree.json（沿用 include/exclude）
        tree_args = argparse.Namespace(
            path=args.path if hasattr(args, 'path') and args.path else '.',
            include=args.include if hasattr(args, 'include') else None,
            exclude=args.exclude if hasattr(args, 'exclude') else None,
            output=os.path.join(default_output_dir, 'tree.json')
        )
        print(f"正在生成 {tree_args.output} ...")
        generate_tree_json(tree_args)
        print(f"已全部生成到 {default_output_dir}/")
    elif args.mode == 'api':
        post_api_mode(args)
    else:
        parser.error("未知的 mode 参数")

if __name__ == '__main__':
    main() 


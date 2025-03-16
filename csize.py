import os
import requests

folder_path = "/Users/yi/YiAi/utils"

def get_folder_files_with_size(folder_path):
    files = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        # 目标字符串不包含数组中的任何一个字符串
        if not any(word in dirpath for word in ['.git']):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                size = os.path.getsize(fp)
                if not any(word in fp for word in ['.DS_Store', '__init__.py', '.png']):
                    # 存储文件路径、文件名和大小
                    files.append((fp, f, size))
    return files

def sort_files_by_size(files):
    return sorted(files, key=lambda x: x[1])

files_with_size = get_folder_files_with_size(folder_path)
sorted_files = sort_files_by_size(files_with_size)

print(f"文件夹 {folder_path} 中的文件按大小排序：")
for file_path, file_name, file_size in sorted_files:
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
    print(f"文件位置为：{file_path}")
    print(f"文件大小为：{file_size} bytes")
    file_name_ary_len = len(file_name.split('.'))
    if file_name_ary_len > 1:
        requests.post(os.getenv('MONGODB_API'), json = {
            "cname": "local",
            "path": f"{file_path}",
            "category": file_name.split('.')[file_name_ary_len - 1],
            "bsize": file_size,
            "text": text
        })
import os
import shutil

def organize_files_by_language(target_dir):
    """
    为目标目录中的每个文件生成目录，目录名取文件路径中语言部分（例如 `java`），
    并将文件移动到对应目录中。

    Args:
        target_dir (str): 目标目录路径。
    """
    # 确保目标目录存在
    if not os.path.exists(target_dir):
        print(f"目录 {target_dir} 不存在！")
        return

    # 遍历目标目录中的所有文件和子目录
    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)

            # 获取目录名，提取语言名
            if os.path.isfile(file_path):
                # 假设语言名称是文件名中的中间部分，用点分隔取第二段
                file_parts = file.split(".")
                if len(file_parts) > 1:
                    language_name = file_parts[0]  # 获取文件名的第一个部分
                else:
                    print(f"无法从文件名提取语言名: {file}")
                    continue

                # 生成新目录路径
                new_dir_path = os.path.join(target_dir, language_name)
                os.makedirs(new_dir_path, exist_ok=True)

                # 移动文件到新目录
                shutil.move(file_path, os.path.join(new_dir_path, file))
                print(f"文件 {file} 已移动到目录 {new_dir_path}")

if __name__ == "__main__":
    # 设置目标目录路径
    target_directory = "/home/corgi/workspace/lian/docs/grammar.js"  # 替换为你的目录路径

    # 调用函数
    organize_files_by_language(target_directory)

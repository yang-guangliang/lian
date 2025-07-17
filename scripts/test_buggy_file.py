#!/usr/bin/env python3

import os
import subprocess
def main():
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 拼接 compiler.sh 的绝对路径
    compiler_abs_path = os.path.join(script_dir, "test.sh")
    compiler_abs_path = os.path.realpath(compiler_abs_path)

    os.system("clear")
    print(script_dir)
    test_dir = os.path.join(os.path.dirname(script_dir), "tests")
    print(test_dir)
    failure_files = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py'):
                print(f"Python 文件: {os.path.join(root, file)}")

                print(f"正在测试文件: {file}")
                file = os.path.join(root, file)
                if not os.path.isfile(file) or 'real_cases' in file:
                    print("文件不存在")
                    continue
                try:
                    # 执行编译脚本并传入测试文件，使用绝对路径
                    result = subprocess.run([compiler_abs_path, file], check=True, text=True, capture_output=True)
                    output = result.stdout + result.stderr
                    if "Error" in output or "error" in output or result.stderr:
                        print(f"测试失败")
                        failure_files.append(file)
                    else:
                        print(f"测试成功")
                except subprocess.CalledProcessError as e:
                    print(f"测试失败，错误信息:\n{e.stderr}")
                    failure_files.append(file)

    print()
    if failure_files:
        print(f"{len(failure_files)} 文件测试失败")
        print("\n".join(failure_files))
    else:
        print("所有测试文件都通过了")

if __name__ == "__main__":
    main()

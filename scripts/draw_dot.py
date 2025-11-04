import os

from graphviz import Source


# 读取dot文件并生成图片
def dot_to_png(dot_file_path, output_png_path=None):
    # 加载dot文件
    src = Source.from_file(dot_file_path)

    # 生成png（默认与dot文件同目录，同名）
    if output_png_path:
        src.render(output_png_path, format='png', cleanup=True)  # cleanup=True删除中间文件
    else:
        src.render(format='png', cleanup=True)
    print(f"PNG图片已生成：{output_png_path or dot_file_path.replace('.dot', '.png')}")


# 示例调用
if __name__ == "__main__":
    path = os.path.dirname(os.path.dirname(__file__))
    dot_file = "tests/lian_workspace/state_flow_graph/58p3.dot"  # dot文件路径
    path = os.path.join(path, dot_file)
    output_png = "output58p3.png"  # 输出png路径（可选）
    dot_to_png(path, output_png)

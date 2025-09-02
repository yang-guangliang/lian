#!/usr/bin/env python3
import argparse
import pandas as pd
import os, glob
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
HTML_FILE = "./dataframe.html"
COUNTER = 0

HTML_CSS = \
"""
<head>
  <title>DataFrame Viewer</title>
  <meta name="viewport" content="width=device-width, maximum-scale=1.0">
  <style>
    .zoom {
        zoom: 90%;
    }
    /* 表格样式 */
    table {
       width: 100%;
       border-collapse: collapse; /* 边框合并 */
       box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
       margin: 20px 0;
       overflow: auto;
    }

    /* 表头样式 */
    th {
       position: sticky;
       top: 0;
       background-color: #4CAF50;
       color: white;
       padding: 4px; /* 减小内边距 */
       line-height: 1.0; /* 减小行高 */
    }

    /* 表格行样式 */
    tr {
       background-color: #fff; /* 设置默认背景颜色 */
       line-height: 1.0; /* 减小行高 */
    }

    tr:nth-child(even) {
       background-color: #f2f2f2; /* 偶数行背景颜色 */
    }

    /* 单元格样式 */
    td, th {
       padding: 4px; /* 减小内边距 */
       text-align: left;
       border-bottom: 1px solid #ddd;
    }

    /* 样式表 */
    .sidebar {
        z-index: 1000;
        font-size: 11px;
        line-height: 1.2;
        height: 100%;
        position: fixed;
        left: 0;
        top: 0;
        background-color: #f1f1f1;
        overflow: hidden;
        overflow-y: auto;
    }
    .sidebar ul {
        list-style-type: none;
        padding: 0;
    }
    .sidebar li {
        padding: 04px;
        cursor: pointer;
    }
    .sidebar li:hover {
        background-color: #ddd;
    }
    .content {
        padding: 02px;
        font-size: 11px;
    }
    .resizer {
        width: 4px;
        height: 100%;
        background-color: #ccc;
        position: absolute;
        right: -5px;
        top: 0;
        cursor: ew-resize;
    }

    /* 鼠标悬停效果 */
    tr:hover {background-color: #ddd;}
    td:hover {background-color: #ddd}
  </style>
</head>
"""
SCRIPT = """
    <script>
        function adjustSidebarWidth() {
            var sidebar = document.querySelector('.sidebar');
            var ul = sidebar.querySelector('ul');
            var li = ul.querySelector('li');
            var maxWidth = li.offsetWidth;
            sidebar.style.width = Math.min(200, window.innerWidth) + 'px';
            var content = document.querySelector('.content');
            content.style.marginLeft = sidebar.style.width;

            document.body.style.zoom = 0.9;
        }

        window.onload = adjustSidebarWidth;
        window.onresize = adjustSidebarWidth;

        function restoreTitle() {
          if (sessionStorage.getItem('pageTitle')) {
            document.title = sessionStorage.getItem('pageTitle');
          }
        }
        document.addEventListener('DOMContentLoaded', restoreTitle);

    </script>
"""

def init():
    # 创建一个解析器来解析命令行参数
    parser = argparse.ArgumentParser(description='Read and print a feather file.')
    parser.add_argument('file_path', type=str, help='The path to the feather file to read.')

    # 解析命令行参数
    args = parser.parse_args()
    # 从命令行参数获取文件路径
    file_path = args.file_path


    global HTML_FILE
    if os.path.isdir(file_path):
        # It's a directory path
        HTML_FILE = os.path.join(file_path, HTML_FILE)
    elif os.path.isfile(file_path):
        # It's a file path
        HTML_FILE = os.path.join(os.path.dirname(file_path), HTML_FILE)

    # 设置pandas的显示选项，以便打印全部内容
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    # os.system('clear')
    with open(HTML_FILE, 'w') as outfile:
        for line in HTML_CSS.splitlines():
            outfile.write(f"{line}\n")

    print("Convert dataframe files to: ", os.path.realpath(HTML_FILE))

    return file_path

def collect_all_file_paths(directory):
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.islink(filepath):
                continue
            if os.path.isfile(filepath):
                file_paths.append(filepath)
    return file_paths

def process_graph_files(all_files, file_path, output_path):
    df = pd.read_feather(file_path)
    # 分组并绘制每个方法的控制流图
    methods = df['method_id'].unique()

    for method in methods:
        method_data = df[df['method_id'] == method]

        # 创建一个有向图
        G = nx.DiGraph()

        # 添加节点和边
        for _, row in method_data.iterrows():
            src = row['src_stmt_id']
            dst = row['dst_stmt_id']
            G.add_node(src)
            if dst != -1:  # 忽略终止节点
                G.add_node(dst)
                G.add_edge(src, dst)

        # 绘制图
        pos = nx.circular_layout(G)  # 布局
        # pos = graphviz_layout(G)  # 布局
        plt.figure()
        nx.draw(G, pos, with_labels=True, node_color='lightblue', arrows=True, width=0.4)
        plt.title(f"Control Flow Graph for Method ID {method}")

        output_path1 = os.path.join(output_path, f"method_{method}.png")
        plt.savefig(output_path1)
        all_files.append(output_path1)
        plt.close()

def read_df(all_files, output_path):
    sidebar = []
    section = []
    for file_path in sorted(all_files, key=os.path.basename):
        global COUNTER

        # [rn]只打印call_path相关
        # suffixes = ["call_graph_p2","call_path_p3","method_id_to_name","class_id_to_name","class_to_method_id","call_beauty","call_beauty2","gir.bundle0"]
        suffixes = ["call_graph_p2","call_path_p3","method_id_to_name","class_id_to_name","class_to_method_id","call_beauty","call_beauty2"]
        if not file_path.endswith(tuple(suffixes)):
            continue

        # 读取并打印单个feather文件
        if file_path.endswith(".indexing"):
            continue
        # if "cfg" in os.path.basename(file_path):
            # process_graph_files(all_files, file_path, output_path)
            # continue

        try:
            df = pd.read_feather(file_path)
        except:
            continue

        if len(df) == 0:
            continue

        content = df.to_html()
        content = content.replace('None', '')
        content = content.replace('NaN', '')

        basename = os.path.basename(file_path)
        sidebar.append(f"\n\t\t\t<li onclick=\"sessionStorage.setItem('pageTitle', '{basename}');document.title='{basename}';window.location.href='#section{COUNTER}'\">{basename}</li>")
        section.append(f"\n\t\t<div id=\"section{COUNTER}\">\n\t\t\t<h1>{file_path}</h1>\n\t\t\t<p>{content}</p>\n\t\t</div>")
        COUNTER += 1
    return sidebar, section

def add_sidebar(sidebar, section):
    with open(HTML_FILE, 'a') as outfile:
        outfile.write("<body>\n\t<div class=\"sidebar\">\n\t\t<ul>")
        for line in sidebar:
            outfile.write(line)
        outfile.write("\n\t\t</ul>\n\n\t</div>")
        outfile.write("\n\t<div class=\"content\">")
        for line in section:
            outfile.write(line)
        outfile.write("</div>")
        outfile.write(SCRIPT)
        outfile.write("</body>")

def add_images(image_paths):
    global COUNTER
    image_section = []
    image_sidebar = []
    prev_image=""
    for image_path in sorted(image_paths, key=os.path.basename):
        if image_path == prev_image:
            continue
        if image_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_sidebar.append(f"\n\t\t\t<li onclick=\"window.location.href='#section{COUNTER}'\">{os.path.basename(image_path)}</li>")
            image_section.append(f"\n\t\t<div id=\"section{COUNTER}\">\n\t\t\t<h1>{os.path.basename(image_path)}</h1>\n\t\t\t<img src=\"{image_path}\" style=\"max-width:100%;height:auto;\">\n\t\t</div>")
            COUNTER += 1
            prev_image = image_path
    return image_section, image_sidebar

if __name__ == "__main__":
    file_path = init()
    all_files = collect_all_file_paths(file_path)
    sidebar, section = read_df(all_files, file_path)

    image_section, image_sidebar = add_images(all_files)
    add_sidebar(sidebar + image_sidebar, section + image_section)

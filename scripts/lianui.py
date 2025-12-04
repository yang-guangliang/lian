import os
import shutil
import streamlit as st
import subprocess
import pandas as pd
import glob
from pathlib import Path
import time

# --- 基础配置 ---
BASE_DIR = Path(__file__).parent.absolute()
# 假设 logo 存在，如果没有可以注释掉
LOGO_PATH = BASE_DIR / "logo.png" if (BASE_DIR / "logo.png").exists() else None
LIAN_PATH = os.path.join(os.path.dirname(BASE_DIR), "src/lian/main.py")
DEFAULT_WORKSPACE = "{in_path}/lian_workspace"

st.set_page_config(
    layout="wide",
    page_title="代码分析工具",
    page_icon=LOGO_PATH,
    initial_sidebar_state="expanded"
)

st.title("🔍 莲花代码分析 LIAN")

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "python", "java", "javascript", "php", "c", "go", "csharp", "ruby", "llvm"
]

# 分析类型选项
ANALYSIS_COMMANDS = {
    "run": "污点分析 (Taint)",
    "lang": "生成通用IR (GIR)",
}

# --- 配置类 (保留你的原始逻辑并微调) ---
class Config:
    def build_sidebar(self):
        with st.sidebar:
            st.header("LIAN配置")
            self.sub_command = st.radio(
                "选择代码分析命令",
                options=list(ANALYSIS_COMMANDS.keys()),
                format_func=lambda x: ANALYSIS_COMMANDS[x]
            )

            st.header("语言 (-l)")
            self.lang = st.multiselect(
                "编程语言选择",
                options=SUPPORTED_LANGUAGES,
                default=[],
                key="lang_sidebar"
            )

            st.header("待分析路径 (in_path)")
            path_option = st.radio("选择输入方式:", ["手动输入", "上传文件"], index=0)

            self.uploaded_files = None
            if path_option == "上传文件":
                self.uploaded_files = st.file_uploader(
                    "上传代码文件",
                    accept_multiple_files=True,
                    help="文件将被保存到临时目录进行分析"
                )
                if self.uploaded_files:
                    if isinstance(self.uploaded_files, list):
                        str_list = [file.name for file in self.uploaded_files]
                        self.in_path = ",".join(str_list)
                    else:
                        self.in_path = self.uploaded_files.name
            else:
                self.in_path = st.text_input(
                    "输入路径",
                    value="",
                    help="要分析的代码路径，可以是文件或目录"
                )

            st.header("其他配置")
            self.quiet = st.checkbox("安静模式 (-q)", value=False)
            self.force = st.checkbox("强制模式 (-f)", value=False)
            self.debug = st.checkbox("调试模式 (-d)", value=False)
            self.print_stmts = st.checkbox("打印语句 (-p)", value=False)
            self.android_mode = st.checkbox("Android 模式 (--android)", value=False)
            self.strict_parse = st.checkbox("严格解析 (--strict-parse-mode)", value=False)
            self.incremental = st.checkbox("增量分析 (-inc)", value=False)
            self.noextern = st.checkbox("禁用外部处理 (--noextern)", value=False)
            self.output_graph = st.checkbox("输出SFG图 (--graph)", value=False)
            self.complete_graph = st.checkbox("输出完整SFG (--complete-graph)", value=False)

            self.workspace = st.text_input("工作空间路径 (-w)", value="{in_path}/lian_workspace")
            self.event_handlers = st.text_input("事件处理器 (-e)", value="")
            self.default_settings = st.text_input("默认设置 (--default-settings)", value="")
            self.additional_settings = st.text_input("额外设置 (--additional-settings)", value="")

            st.divider()
            st.markdown("🌐 [项目地址](https://github.com/yang-guangliang/lian)")

    def build_command(self):
        cmd = ["python", LIAN_PATH, self.sub_command]

        if self.lang:
            cmd.extend(["-l", ",".join(self.lang)])

        # 参数映射
        flags = [
            ("-q", self.quiet),
            ("-f", self.force),
            ("-d", self.debug),
            ("-p", self.print_stmts),
            ("--android", self.android_mode),
            ("--strict-parse-mode", self.strict_parse),
            ("-inc", self.incremental),
            ("--noextern", self.noextern),
            ("--graph", self.output_graph),
            ("--complete-graph", self.complete_graph),
        ]
        for flag, condition in flags:
            if condition:
                cmd.append(flag)

        options = [
            ("-w", self.workspace, DEFAULT_WORKSPACE),
            ("-e", self.event_handlers, ""),
            ("--default-settings", self.default_settings, ""),
            ("--additional-settings", self.additional_settings, ""),
        ]
        for flag, condition, default in options:
            if condition and condition != default:
                cmd.extend([flag, condition])

        cmd.append(self.in_path)

        return cmd

# --- 实例化配置 ---
config = Config()
config.build_sidebar()

# Initialize session state for the button
if "analyze_clicked" not in st.session_state:
    st.session_state.analyze_clicked = False

st.markdown("### 🚀 执行控制台")

# 1. 运行按钮与命令预览
col1, col2 = st.columns([1, 4])
with col1:
    run_btn = st.button("开始分析", type="primary", use_container_width=True)

if run_btn:
    st.session_state.analyze_clicked = True
    run_btn = None

if st.session_state.analyze_clicked:
    st.session_state.analyze_clicked = False

    cmd = config.build_command()
    if cmd:
        # 将列表转为字符串显示
        cmd_str = " ".join(cmd)
        st.code(cmd_str, language="bash")

    st.divider()

    # 创建可展开的日志监控区域
    with st.expander("📝 实时日志监控 (点击展开/折叠)", expanded=True):
        log_container = st.empty()
        full_logs = []

        try:
            #print(cmd)
            # 使用 Popen 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # 将错误重定向到标准输出
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 实时读取输出
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    full_logs.append(line)
                    # 为了性能，每接收几行或者每隔一点时间刷新一次UI会更好，
                    # 这里为了简单直接刷新最后20行
                    log_text = "".join(full_logs[-20:])
                    log_container.text_area(
                        "实时日志",
                        value=log_text,
                        height=300,  # 设置高度为 300 像素
                    )

            if process.returncode == 0:
                st.success("✅ 分析执行完毕！")
            else:
                st.error(f"❌ 分析出错，返回码: {process.returncode}")

        except Exception as e:
            st.error(f"执行过程中发生异常: {str(e)}")

    # 3. 结果可视化展示
    st.divider()
    st.markdown("### 📊 分析结果展示")

    # 检查工作空间是否存在
    workspace_path = Path(config.workspace)

    if not workspace_path.exists():
        st.info(f"等待分析结果... (工作空间 '{config.workspace}' 尚未创建)")
    else:
        st.write(f"正在从工作空间读取结果: `{workspace_path.absolute()}`")

        # 查找工作空间内的所有 CSV 文件 (假设结果以 CSV 格式存储)
        # 如果你的工具生成的是 excel 或 json，请相应修改后缀
        result_files = list(workspace_path.glob("**/*.csv"))

        if not result_files:
            st.warning("工作空间中未找到 CSV 结果文件。")
        else:
            # 使用 Tabs 对不同文件进行分类展示
            file_names = [f.name for f in result_files]
            tabs = st.tabs(file_names)

            for i, file_path in enumerate(result_files):
                with tabs[i]:
                    try:
                        df = pd.read_csv(file_path)

                        st.markdown(f"**文件路径**: `{file_path}`")
                        st.markdown(f"**数据行数**: {len(df)}")

                        # 交互式 DataFrame
                        st.dataframe(df, use_container_width=True)

                        # 简单的下载按钮
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"下载 {file_path.name}",
                            data=csv,
                            file_name=file_path.name,
                            mime='text/csv',
                        )
                    except Exception as e:
                        st.error(f"无法读取文件 {file_path.name}: {e}")

        # 如果有 .dot 文件 (Graphviz)，也可以尝试展示
        dot_files = list(workspace_path.glob("**/*.dot"))
        if dot_files and config.output_graph:
            st.markdown("#### 🕸️ 状态流图 (SFG)")
            dot_tabs = st.tabs([f.name for f in dot_files])
            for i, dot_file in enumerate(dot_files):
                with dot_tabs[i]:
                    try:
                        with open(dot_file, "r") as f:
                            dot_source = f.read()
                        st.graphviz_chart(dot_source)
                    except Exception as e:
                        st.error(f"无法渲染图表: {e}")
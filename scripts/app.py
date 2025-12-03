import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide", page_title="代码分析工具")

st.title("🔍莲花代码分析LIAN")

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "python",
    "java",
    "javascript",
    "php",
    "c",
    "go",
    "csharp",
    "ruby",
    "llvm"
]

class Config:
    def build_sidebar(self):
        # 侧边栏: 通用参数
        with st.sidebar:
            st.header("LIAN配置")

            self.lang = st.multiselect(
                "编程语言 (-l)",
                options=SUPPORTED_LANGUAGES,
                default=[],
                help="选择要分析的编程语言，可多选",
                key="lang_sidebar"
            )

            st.subheader("输入路径选择")
            path_option = st.radio(
                "选择输入方式:",
                ["手动输入", "选择文件", ],
                index=0,
                help="选择输入路径的方式"
            )
            self.in_path = ""
            if path_option == "选择文件":
                uploaded_file = st.file_uploader(
                    "选择文件",
                    accept_multiple_files=True,
                    help="选择要分析的单个代码文件"
                )
                if uploaded_file is not None:
                    if isinstance(uploaded_file, list):
                        self.in_path = [Path(file.name) for file in uploaded_file]
                    else:
                        st.success(f"已选择文件: {uploaded_file.name}")
                        self.in_path = uploaded_file.name
            else:
                self.in_path = st.text_input(
                    "输入路径 (in_path)",
                    value="",
                    help="要分析的代码路径，可以是文件或目录，以逗号隔开"
                )

            self.workspace = st.text_input("工作空间 (-w)", value="lian_workspace", help="工作空间目录，用于存储分析结果（默认：lian_workspace）")

            st.divider()
            self.quiet = st.checkbox("安静模式 (-q)", value=False, help="禁用详细输出，减少控制台信息")
            self.force = st.checkbox("强制模式 (-f)", value=False, help="启用强制模式，重写工作空间目录")
            self.debug = st.checkbox("调试模式 (-d)", value=False, help="启用调试模式，输出详细调试信息")
            self.print_stmts = st.checkbox("打印语句 (-p)", value=False, help="打印解析后的语句信息")

            #included_headers = st.text_input("包含头文件 (-i)", value="", help="指定C语言风格的头文件路径")
            #enable_header_preprocess = st.checkbox("启用头文件预处理 (-I)", value=False, help="处理C语言风格的头文件")
            self.android_mode = st.checkbox("Android 模式 (--android)", value=False, help="启用Android分析模式")
            self.strict_parse = st.checkbox("严格解析 (--strict-parse-mode)", value=False, help="启用严格的代码解析方式")
            self.incremental = st.checkbox("增量分析 (-inc)", value=False, help="重用之前的分析结果（GIR、作用域和CFG）")
            self.noextern = st.checkbox("禁用外部处理 (--noextern)", value=False, help="禁用外部处理模块")
            self.output_graph = st.checkbox("输出 SFG 图 (--graph)", value=False, help="输出状态流图（SFG）到.dot文件")
            self.complete_graph = st.checkbox("完整图信息 (--complete-graph)", value=False, help="输出包含每个节点更详细信息的状态流图")

            #self.cores = st.number_input("CPU 核心数 (-c)", min_value=1, value=1, help="配置可用的CPU核心数")

            st.divider()
            self.event_handlers = st.text_input("事件处理器 (-e)", value="", help="配置事件处理器目录")
            self.default_settings = st.text_input("默认设置文件夹 (--default-settings)", value="", help="指定默认设置文件夹路径")
            self.additional_settings = st.text_input("额外设置文件夹 (--additional-settings)", value="", help="指定额外设置文件夹路径")

config = Config()
config.build_sidebar()


# 主界面: 子命令选择
tab1, tab2, tab3, tab4 = st.tabs([
    "▶️ Run (端到端分析)",
    "📝 Lang (生成IR)",
    "🧠 Semantic (语义分析)",
    "🔒 Taint (污点分析)"
])

def build_command(subcommand, **kwargs):
    """构建命令行"""
    cmd = ["./your_tool", subcommand]

    # 添加通用参数
    if quiet:
        cmd.append("-q")
    cmd.extend([in_path])
    cmd.extend(["-w", workspace])
    if force:
        cmd.append("-f")
    if debug:
        cmd.append("-d")
    cmd.extend(["-c", str(cores)])

    if included_headers:
        cmd.extend(["-i", included_headers])
    if enable_header_preprocess:
        cmd.append("-I")
    if print_stmts:
        cmd.append("-p")
    if android_mode:
        cmd.append("--android")
    if event_handlers:
        cmd.extend(["-e", event_handlers])
    if strict_parse:
        cmd.append("--strict-parse-mode")
    if incremental:
        cmd.append("-inc")
    if default_settings:
        cmd.extend(["--default-settings", default_settings])
    if additional_settings:
        cmd.extend(["--additional-settings", additional_settings])
    if output_graph:
        cmd.append("--graph")
    if complete_graph:
        cmd.append("--complete-graph")
    if noextern:
        cmd.append("--noextern")

    # 添加子命令特定参数
    for key, value in kwargs.items():
        if value is not None and value != "":
            if isinstance(value, bool) and value:
                cmd.append(f"--{key.replace('_', '-')}")
            elif not isinstance(value, bool):
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    return cmd


# Tab 1: Run
with tab1:
    st.header("端到端分析")
    st.info("运行完整的分析流程")

    if st.button("🚀 执行 Run", type="primary"):
        cmd = build_command("run")
        st.code(" ".join(cmd), language="bash")
        # 执行逻辑...

# Tab 2: Lang
with tab2:
    st.header("生成通用 IR")
    st.info("将代码解析为中间表示(IR)")

    lang = st.text_input("编程语言 (-l)", value="",
                         help="例如: python, java, c++", key="lang")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 执行 Lang", type="primary", use_container_width=True):
            cmd = build_command("lang", l=lang)
            st.code(" ".join(cmd), language="bash")

            with st.spinner("正在生成 IR..."):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    st.success("✅ 执行成功!")

                    # 这里读取输出的 DataFrame
                    # df = pd.read_pickle(workspace + "/output.pkl")
                    # st.dataframe(df)

                except subprocess.CalledProcessError as e:
                    st.error(f"❌ 执行失败: {e.stderr}")

# Tab 4: Taint
with tab4:
    st.header("污点分析")
    st.info("追踪数据流和潜在的安全问题")

    taint_sources = st.text_area("污点源", help="每行一个源", key="taint_sources")
    taint_sinks = st.text_area("污点汇", help="每行一个汇", key="taint_sinks")

    if st.button("🚀 执行 Taint", type="primary"):
        cmd = build_command("taint")
        st.code(" ".join(cmd), language="bash")
        # 执行逻辑...


# 底部: 显示结果
st.divider()
st.header("📊 分析结果")

# 检查是否有输出文件
output_file = Path(workspace) / "output.pkl"
if output_file.exists():
    df = pd.read_pickle(output_file)

    # 数据概览
    col1, col2, col3 = st.columns(3)
    col1.metric("总行数", len(df))
    col2.metric("列数", len(df.columns))
    col3.metric("内存占用", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 数据表格
    st.dataframe(df, use_container_width=True, height=400)

    # 下载按钮
    st.download_button(
        "💾 下载结果",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="result.csv",
        mime="text/csv"
    )
else:
    st.info("暂无分析结果,请先执行分析命令")
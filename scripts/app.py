import os
import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
import collections

# --- 基础配置 ---
BASE_DIR = Path(__file__).parent.absolute()
# 假设 logo 存在，如果没有可以注释掉
LOGO_PATH = BASE_DIR / "logo.png" if (BASE_DIR / "logo.png").exists() else None
LIAN_PATH = os.path.join(os.path.dirname(BASE_DIR), "src/lian/main.py")
DEFAULT_WORKSPACE = "/tmp/lian_workspace"

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "python", "java", "javascript", "php", "c", "go", "csharp", "ruby", "llvm"
]

# 分析类型选项
ANALYSIS_COMMANDS = {
    "run": "污点分析 (Taint)",
    "lang": "生成通用IR (GIR)",
}

IGNORED_EXTENSIONS = [".indexing"]
TXT_EXTENSIONS = [".txt", ".dot"]


# 定义日志展示行数限制（防止浏览器卡死）
MAX_DISPLAY_LINES = 40
UPDATE_FREQ = 10

# --- 配置类 (保留你的原始逻辑并微调) ---
class Render:
    def __init__(self) -> None:
        self.workspace = DEFAULT_WORKSPACE
        self.in_path = ""

    def config_logo(self):
        st.set_page_config(
            layout="wide",
            page_title="代码分析工具",
            page_icon=LOGO_PATH,
            initial_sidebar_state="expanded"
        )

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
                in_path_input = st.text_input(
                    "输入路径",
                    value=self.in_path,
                    help="要分析的代码路径，可以是文件或目录"
                )
                if in_path_input != self.in_path:
                    self.in_path = in_path_input
                    # 当in_path改变时，自动更新workspace
                    if self.in_path:
                        if "lian_workspace" not in self.in_path:
                            self.workspace = os.path.join(self.in_path, "lian_workspace")
                        else:
                            self.workspace = self.in_path


            st.header("其他配置")
            self.workspace = st.text_input("工作空间路径 (-w)", value=DEFAULT_WORKSPACE)

            self.force = st.checkbox("强制模式 (-f)", value=False)
            self.debug = st.checkbox("调试模式 (-d)", value=False)
            self.print_stmts = st.checkbox("打印语句 (-p)", value=False)
            self.android_mode = st.checkbox("Android 模式 (--android)", value=False)
            self.strict_parse = st.checkbox("严格解析 (--strict-parse-mode)", value=False)
            self.incremental = st.checkbox("增量分析 (-inc)", value=False)
            self.noextern = st.checkbox("禁用外部处理 (--noextern)", value=True)
            self.output_graph = st.checkbox("输出SFG图 (--graph)", value=False)
            self.complete_graph = st.checkbox("输出完整SFG (--complete-graph)", value=False)

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

        self.cmd = cmd

        return cmd

    def create_log_container(self):
        # 创建一个用于展示分析状态的 st.status 容器
        status_box = st.empty()
        status_box.info("准备开始分析...")

        # 用于保存完整日志的列表
        full_log_content = []

        # 用于界面显示的滚动缓冲区（只保留最后 N 行）
        log_buffer = collections.deque(maxlen=MAX_DISPLAY_LINES)

        # 计数器
        line_counter = 0

        # 创建一个可折叠的区域来显示日志细节
        with st.expander(f"⚙️ 分析控制台输出 (实时刷新，显示最近 {MAX_DISPLAY_LINES} 行)", expanded=False) as log_expander:
            # 创建一个占位符用于实时刷新日志
            log_placeholder = st.empty()
            log_text = ""

            try:
                status_box.info("🚀 正在启动 LIAN 分析...")

                # 使用 Popen 而不是 run，实现流式读取
                process = subprocess.Popen(
                    self.cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,  # 行缓冲
                    encoding='utf-8',
                    errors='replace' # 替换无法解码的字符，防止崩溃
                )

                # 实时读取输出
                while True:
                    line = process.stdout.readline()

                    # 如果进程结束且没有新行了，跳出
                    if not line and process.poll() is not None:
                        break

                    if line:
                        # 1. 存入完整日志和缓冲区
                        line = line.rstrip()

                        if "<Workspace directory> :" in line:
                            workspace_dir = line.split(":")[1].strip()
                            self.workspace = workspace_dir

                        full_log_content.append(line)
                        log_buffer.append(line)

                        # 2. 根据日志内容更新主状态 (例如：进度指示)
                        if "######" in line:
                            # 重要的阶段性输出，直接显示在主状态栏
                            status_box.write(line)

                        line_counter += 1

                        # 3. 刷新 UI，避免过于频繁，导致浏览器卡顿
                        if line_counter % UPDATE_FREQ == 0:
                            log_text = "\n".join(log_buffer)
                            log_placeholder.code(log_text, language="bash")

                # --- 循环结束后 ---
                # 4. 强制最后刷新一次，确保所有日志都显示
                log_text = "\n".join(log_buffer)
                log_placeholder.code(log_text, language="bash")

                # 等待进程完全结束获取返回码
                return_code = process.wait()

                # 运行结束后的逻辑：更新 st.status 状态
                if return_code == 0:
                    status_box.success("✅ 分析完成！")
                else:
                    status_box.error(f"❌ 分析异常终止 (Exit Code: {return_code})")

            except Exception as e:
                status_box.error(f"❌ 执行错误: {str(e)}")
                st.exception(e) # 显示详细的 Python 异常堆栈

        # --- 日志完整显示 ---
        if full_log_content and len(full_log_content) > MAX_DISPLAY_LINES:
            full_log_str = "\n".join(full_log_content)

            # # 下载按钮放在醒目位置
            # st.download_button(
            #     label="💾 下载完整日志文件",
            #     data=full_log_str,
            #     file_name="lian_analysis_log.txt",
            #     mime="text/plain",
            #     use_container_width=True,
            #     type="secondary"
            # )

            # 创建一个可展开的区域来显示完整日志
            with st.expander("点击查看全部控制台输出（完整内容）", expanded=False):
                st.code(full_log_str, language="bash")

        return True

    def read_dataframe(self, file_path: Path):
        try:
            return pd.read_feather(file_path)
        except:
            return ""

    def display_as_text(self, file_path: Path):
        """显示文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            st.code(content, language="text")
        except Exception as e:
            st.error(f"无法读取文件: {e}")

    def render_results(self):
        # 检查并处理工作空间路径
        # 检查并处理工作空间路径
        workspace_path = Path(self.workspace)

        if not workspace_path.exists():
            st.info(f"等待分析完成... 工作空间 `{self.workspace}` 尚未找到。")
            return

        search_query = st.text_input(
            "🔍 在结果中过滤文件或目录",
            key="results_search_box"
        ).lower()

        # 查找所有文件 (不再过滤后缀)
        result_dirs_map = collections.defaultdict(list) # {dir_path: [file_paths]}

        for root, _, files in os.walk(self.workspace):
            current_root = Path(root)
            for file in files:
                flag = True
                for ext in IGNORED_EXTENSIONS:
                    if file.endswith(ext):
                        flag = False
                        continue
                if not flag:
                    continue

                if str(current_root).endswith("/src"):
                    continue

                file_path = current_root / file

                # 检查是否匹配搜索关键词
                file_name_lower = file.lower()
                dir_name_lower = current_root.name.lower()

                if not search_query or search_query in file_name_lower or search_query in dir_name_lower:
                    result_dirs_map[current_root].append(file_path)

        if not result_dirs_map:
            if search_query:
                 st.warning(f"在工作空间中未找到与关键词 '{search_query}' 匹配的文件。")
            else:
                 st.warning("工作空间中未发现任何文件。")
            return

        # 1. 目录层设计 (Tabs)
        sorted_dirs = sorted(list(result_dirs_map.keys()))

        tabs_map = {}
        for d in sorted_dirs:
            relative_path = d.relative_to(workspace_path)
            tab_name = str(relative_path) if str(relative_path) != '.' else workspace_path.name

            if tab_name in tabs_map:
                 tab_name = f"{d.parent.name}/{d.name}"

            tabs_map[tab_name] = d

        tab_names_list = list(tabs_map.keys())
        dir_tabs = st.tabs(tab_names_list)

        # 2. 文件层设计 (Tabs)
        for idx, tab_name in enumerate(tab_names_list):
            dir_path = tabs_map[tab_name]

            with dir_tabs[idx]:
                dir_files = sorted(result_dirs_map[dir_path])
                file_names = [f.name for f in dir_files]

                if not file_names:
                    continue

                file_tabs = st.tabs(file_names)
                for file_idx, file_name in enumerate(file_names):
                    file_path = dir_files[file_idx]

                    with file_tabs[file_idx]:
                        st.markdown(f"**文件路径**: `{file_path}`")

                        # --- 核心：直接加载内容 (使用 spinner 提升用户体验) ---
                        with st.spinner(f"正在加载 {file_name} ({file_path.suffix.upper()})..."):
                            # 1. 尝试作为 DataFrame/Feather 加载
                            if file_path.suffix.lower() not in TXT_EXTENSIONS:
                                try:
                                    df = self.read_dataframe(file_path)
                                    st.dataframe(df, use_container_width=True)
                                except Exception as e:
                                    #st.error(f"无法将 {file_name} 加载为 DataFrame/Feather 格式：{e}")
                                    st.warning("尝试作为文本显示...")
                                    self.display_as_text(file_path)

                            # 2. 尝试作为文本/代码加载 (对于日志, dot 文件等)
                            else:
                                self.display_as_text(file_path)


# --- 主界面逻辑 ---
def main():
    st.title("🔍 莲花代码分析 (LIAN)")

    render = Render()
    render.config_logo()
    render.build_sidebar()

    # 执行按钮
    if st.button("开始分析", type="primary", use_container_width=True):
        cmd_list = render.build_command()
        st.code(" ".join(cmd_list), language="bash")

        # 执行与日志输出区域
        #st.divider()
        st.subheader("执行日志")
        render.create_log_container()

    st.subheader("分析结果可视化")
    render.render_results()

if __name__ == "__main__":
    main()
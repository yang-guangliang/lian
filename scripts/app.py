import os
import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
import collections
import base64

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
    "semantic": "语义分析 (Semantic)",
    "lang": "生成通用IR (GIR)",
}

IGNORED_EXTENSIONS = [".log", ".indexing"]
TXT_EXTENSIONS = [".txt", ".dot"]
IGNORED_DIRS = ["externs", "src"]

SORTED_DIRS = [
    "frontend",
    "semantic_p1",
    "semantic_p2",
    "semantic_p3"
]

# 定义日志展示行数限制（防止浏览器卡死）
MAX_DISPLAY_LINES = 40
UPDATE_FREQ = 10
DATAFRAME_HEIGHT = 600
FOOTER_HEIGHT = 64
MIN_FOOTER_HEIGHT = 0
MAX_FOOTER_HEIGHT = FOOTER_HEIGHT

class Render:
    def __init__(self) -> None:
        self.workspace = DEFAULT_WORKSPACE
        self.in_path = ""

    def is_ignored_file(self, path):
        for ext in IGNORED_EXTENSIONS:
            if path.endswith(ext):
                return True
        return False

    def is_ignored_dir(self, path):
        for dir_name in IGNORED_DIRS:
            if f"/{dir_name}/" in path or path.endswith(f"/{dir_name}") or path.startswith(f"{dir_name}/") or path == dir_name:
                return True
        return False

    def config_layout(self, page_title="代码分析工具"):
        st.set_page_config(
            layout="wide",
            page_title=page_title,
            page_icon=LOGO_PATH,
            initial_sidebar_state="expanded"
        )

    def config_css(self):
        st.markdown("""
        <style>
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap;
                row-gap: 0px;
            }

            div[role="radiogroup"] {
                flex-wrap: wrap;
            }

            pre code {
                white-space: pre-wrap !important;
                word-break: break-all !important;
            }
        </style>
        """, unsafe_allow_html=True)

    def config_title(self):
        if LOGO_PATH:
            with open(LOGO_PATH, "rb") as f:
                img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            header_html = f"""
            <div style=\"display:flex;align-items:center;gap:12px;margin-bottom:1rem;\">
                <img src=\"data:image/png;base64,{img_b64}\" style=\"height:36px;\" />
                <h1 style=\"margin:0;\">莲花代码分析 (LIAN)</h1>
            </div>
            """
            st.markdown(header_html, unsafe_allow_html=True)
        else:
            st.title("莲花代码分析 (LIAN)")

    def build_sidebar(self):
        from_btn_flag = False
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                st.header("配置")

            self.sub_command = st.radio(
                "选择代码分析命令",
                options=list(ANALYSIS_COMMANDS.keys()),
                format_func=lambda x: ANALYSIS_COMMANDS[x]
            )

            #st.header("语言 (-l)")
            self.lang = st.multiselect(
                "语言 (-l)",
                options=SUPPORTED_LANGUAGES,
                default=[],
                key="lang_sidebar"
            )

            #st.header("待分析路径 (in_path)")
            in_path_input = st.text_input(
                "待分析路径 (in_path)",
                value=self.in_path,
                help="要分析的代码路径，可以是文件或目录"
            )
            if in_path_input != self.in_path:
                self.in_path = in_path_input

            st.header("其他配置")
            self.workspace = st.text_input("工作空间路径 (-w)", value=self.workspace)

            self.display_full_log = st.checkbox("显示完整日志", value=False)
            self.reset_tabs = st.checkbox("重置结果视图", value=False)
            self.force = st.checkbox("强制模式 (-f)", value=False)
            self.debug = st.checkbox("调试模式 (-d)", value=False)
            self.output_graph = st.checkbox("输出SFG图 (--graph)", value=False)
            self.complete_graph = st.checkbox("输出完整SFG (--complete-graph)", value=False)

            self.print_stmts = st.checkbox("打印语句 (-p)", value=False)
            #self.android_mode = st.checkbox("Android 模式 (--android)", value=False)
            #self.strict_parse = st.checkbox("严格解析 (--strict-parse-mode)", value=False)
            self.incremental = st.checkbox("增量分析 (-inc)", value=False)
            self.noextern = st.checkbox("禁用外部处理 (--noextern)", value=True)

            self.event_handlers = st.text_input("事件处理器 (-e)", value="")
            self.default_settings = st.text_input("默认设置 (--default-settings)", value="")
            self.additional_settings = st.text_input("额外设置 (--additional-settings)", value="")

            st.divider()
            st.markdown("查看[项目源代码](https://github.com/yang-guangliang/lian)")
            st.markdown("本项目由[复旦大学系统安全与可靠性研究组](https://gitee.com/fdu-ssr/)开发和维护")

            with col2:
                # 执行按钮
                if st.button("运行", type="primary", width='stretch'):
                    cmd_list = self.build_command()
                    st.session_state.last_cmd = " ".join(cmd_list)
                    from_btn_flag = True

        return from_btn_flag

    def build_command(self):
        cmd = ["python", LIAN_PATH, self.sub_command]

        if self.lang:
            cmd.extend(["-l", ",".join(self.lang)])

        # 参数映射
        flags = [
            ("-f", self.force),
            ("-d", self.debug),
            ("-p", self.print_stmts),
            #("--android", self.android_mode),
            #("--strict-parse-mode", self.strict_parse),
            ("-inc", self.incremental),
            ("--noextern", self.noextern),
            ("--graph", self.output_graph),
            ("--complete-graph", self.complete_graph),
        ]
        for flag, condition in flags:
            if condition:
                cmd.append(flag)

        # 始终传递工作空间路径 (-w)，避免依赖后端默认值
        if self.workspace:
            cmd.extend(["-w", self.workspace])

        options = [
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

    def create_log_container_with_result(self, from_btn_flag: bool = False):
        """执行命令并返回日志内容和状态，用于保存到 session_state"""
        st.subheader(f"执行日志")
        if not from_btn_flag:
            if "full_log" in st.session_state:
                #st.info("分析完毕")
                with st.expander(f"⚙️ 日志记录", expanded=self.display_full_log):
                    if self.display_full_log:
                        st.code(st.session_state.full_log, language="bash")
                    else:
                        log_lines = st.session_state.full_log.splitlines()
                        recent_lines = log_lines[-MAX_DISPLAY_LINES:] if len(log_lines) > MAX_DISPLAY_LINES else log_lines
                        st.code("\n".join(recent_lines), language="bash")
                        #del st.session_state.full_log
            return "", ""

        status_box = st.empty()
        status_box.info("准备开始分析...")

        full_log_content = []
        log_buffer = collections.deque(maxlen=MAX_DISPLAY_LINES)
        line_counter = 0
        result_status = "success"

        expander_flag = False
        expander_str = f"⚙️ 控制台输出 (显示最近 {MAX_DISPLAY_LINES} 行)"
        if self.display_full_log:
            expander_flag = True
            expander_str = f"⚙️ 控制台输出"

        with st.expander(expander_str, expanded=expander_flag):
            log_placeholder = st.empty()

            try:
                status_box.info("🚀 正在启动 LIAN 分析...")

                process = subprocess.Popen(
                    self.cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding='utf-8',
                    errors='replace'
                )

                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break

                    if line:
                        line = line.rstrip()
                        if "<Workspace directory> :" in line:
                            workspace_dir = line.split(":")[1].strip()
                            self.workspace = workspace_dir

                        full_log_content.append(line)
                        log_buffer.append(line)

                        if "######" in line:
                            status_box.write(line)

                        line_counter += 1
                        if line_counter % UPDATE_FREQ == 0:
                            if self.display_full_log:
                                log_placeholder.code("\n".join(full_log_content), language="bash")
                            else:
                                log_placeholder.code("\n".join(log_buffer), language="bash")

                if self.display_full_log:
                    log_placeholder.code("\n".join(full_log_content), language="bash")
                else:
                    log_placeholder.code("\n".join(log_buffer), language="bash")

                return_code = process.wait()

                if return_code == 0:
                    status_box.success("✅ 分析完成！")
                    result_status = "success"
                else:
                    status_box.error(f"❌ 分析异常终止 (Exit Code: {return_code})")
                    result_status = "error"

            except Exception as e:
                status_box.error(f"❌ 执行错误: {str(e)}")
                result_status = "error"

            # 如果日志的长度超过了允许显示的长度，那么提供查看选项
            st.session_state.full_log = "\n".join(full_log_content)
            if not self.display_full_log and len(full_log_content) > MAX_DISPLAY_LINES:
                # 创建两个按钮供用户选择
                col1, col2 = st.columns(2)

                with col1:
                    # 在新页面中查看完整日志
                    st.button("📄 在新页面查看完整日志", width='stretch')

                with col2:
                    # 下载日志文件
                    st.download_button(
                        label="💾 下载日志文件",
                        data="\n".join(full_log_content),
                        file_name="lian_analysis.log",
                        mime="text/plain",
                        width='stretch'
                    )

        log_str = "\n".join(log_buffer) if log_buffer else ""
        return log_str, result_status

    def read_dataframe(self, file_path: Path):
        return pd.read_feather(file_path)

    def render_dataframe_with_search(self, df, key_suffix):
        """渲染带有高级检索功能的 DataFrame"""
        # --- DataFrame 高级检索功能 ---
        with st.expander("🔍 数据检索与过滤", expanded=False):
            col1, col2 = st.columns([1, 2])
            with col1:
                search_cols = st.multiselect(
                    "限制检索列 (留空则检索所有列)",
                    options=df.columns.tolist(),
                    default=[],
                    key=f"cols_{key_suffix}"
                )
            with col2:
                search_term = st.text_input(
                    "输入检索内容 (支持部分匹配)",
                    key=f"search_{key_suffix}"
                )

        # 执行过滤逻辑
        if search_term:
            target_cols = search_cols if search_cols else df.columns

            # 构建查询条件
            mask = pd.DataFrame(False, index=df.index, columns=target_cols)
            for col in target_cols:
                mask[col] = df[col].astype(str).str.contains(search_term, case=False, na=False)

            final_mask = mask.any(axis=1)
            filtered_df = df[final_mask]

            st.info(f"检索到 {len(filtered_df)} / {len(df)} 行数据")
            st.dataframe(filtered_df, width='stretch', height=DATAFRAME_HEIGHT)
        else:
            st.dataframe(df, width='stretch', height=DATAFRAME_HEIGHT)

    def display_as_text(self, file_path: Path):
        """显示文本文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            st.code(content, language="text")
        except Exception as e:
            st.error(f"无法读取文件: {e}")

    def render_results(self):
        st.subheader("分析结果可视化")

        # 检查并处理工作空间路径
        workspace_path = Path(self.workspace)

        if not workspace_path.exists():
            st.info(f"等待分析完成... 工作空间 `{self.workspace}` 尚未找到。")
            return

        search_query = st.text_input(
            "🔍 在结果中过滤文件或目录",
            key="results_search_box"
        ).lower()

        # 查找所有文件
        result_dirs_map = collections.defaultdict(list) # {dir_path: [file_paths]}

        for root, _, files in os.walk(self.workspace):
            current_root = Path(root)
            current_root_str = str(current_root)

            # 过滤工作空间中的 src 根目录和所有 externs 相关目录
            if self.is_ignored_dir(current_root_str):
                continue

            for file in files:
                # 扩展名过滤
                if self.is_ignored_file(file):
                    continue

                file_path = current_root / file

                # 检查是否匹配搜索关键词
                if not search_query or search_query in file.lower() or search_query in current_root.name.lower():
                    result_dirs_map[current_root].append(file_path)

        if not result_dirs_map:
            if search_query:
                 st.warning(f"在工作空间中未找到与关键词 '{search_query}' 匹配的文件。")
            else:
                 st.warning("工作空间中未发现任何文件。")
            return

        # 1. 目录层设计 (Tabs)
        sorted_dirs = sorted(
            list(result_dirs_map.keys()),
            key=lambda d: (
                # Priority order for specific directories
                SORTED_DIRS.index(d.name)
                if d.name in SORTED_DIRS
                else float('inf'),  # Other directories go after
                d.name  # Secondary sort by name
            )
        )

        tabs_map = {}
        for d in sorted_dirs:
            relative_path = d.relative_to(workspace_path)
            tab_name = str(relative_path) if str(relative_path) != '.' else workspace_path.name

            if tab_name in tabs_map:
                 tab_name = f"{d.parent.name}/{d.name}"

            tabs_map[tab_name] = d

        tab_names_list = list(tabs_map.keys())
        tab_name = st.radio("目录", options=tab_names_list, index=0, horizontal=True)

        # 2. 文件层设计：下拉选择 + 内容展示
        dir_path = tabs_map[tab_name]
        files_with_names = {f.name: f for f in result_dirs_map[dir_path]}
        file_names = sorted(list(files_with_names.keys()))

        if len(file_names) == 0:
            return

        # 文件选择组件
        selected_file = st.selectbox(
            f"选择文件 ({len(file_names)} 个文件)",
            options=["请选择文件..."] + file_names,
            key=f"file_select_{tab_name}",
            index=1 if len(file_names) == 1 else 0
        )

        file_path_str = files_with_names.get(selected_file, None)
        if not file_path_str:
            self.build_footer()
            return

        file_path = Path(file_path_str)

        st.markdown(f"**文件路径**: `{file_path}`")
        self.config_layout(page_title=f"{tab_name}/{file_path.name}")


        with st.spinner(f"正在加载 {file_path.name} ({file_path.suffix.upper()})..."):
            if file_path.suffix.lower() in TXT_EXTENSIONS:
                self.display_as_text(file_path)
            else:
                try:
                    df = self.read_dataframe(file_path)
                    self.render_dataframe_with_search(df, f"{tab_name}_{file_path.name}")
                except Exception as e:
                    st.warning("尝试作为文本显示...")
                    self.display_as_text(file_path)

    def build_footer(self, space_height=FOOTER_HEIGHT):
        st.markdown(f"""
        <div style="min-height: {space_height}vh;"></div>
        """, unsafe_allow_html=True)

# --- 主界面逻辑 ---
def main():
    render = Render()
    render.config_css()
    render.config_layout()
    render.config_title()
    from_btn_flag = render.build_sidebar()

    if render.reset_tabs:
        for key in st.session_state.keys():
            if key.startswith("file_select_"):
                st.session_state[key] = None

    if "last_cmd" in st.session_state:
        st.code(st.session_state.last_cmd, language="bash")

    # 执行并保存日志
    render.create_log_container_with_result(from_btn_flag)
    render.render_results()
    #render.build_footer()

if __name__ == "__main__":
    main()

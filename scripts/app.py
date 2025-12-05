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
    "lang": "生成通用IR (GIR)",
}

IGNORED_EXTENSIONS = []
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


            st.header("其他配置")
            self.workspace = st.text_input("工作空间路径 (-w)", value=self.workspace)

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

    def create_log_container_with_result(self):
        """执行命令并返回日志内容和状态，用于保存到 session_state"""
        status_box = st.empty()
        status_box.info("准备开始分析...")

        full_log_content = []
        log_buffer = collections.deque(maxlen=MAX_DISPLAY_LINES)
        line_counter = 0
        result_status = "success"

        with st.expander(f"⚙️ 分析控制台输出 (实时刷新，显示最近 {MAX_DISPLAY_LINES} 行)", expanded=False):
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
                            log_placeholder.code("\n".join(log_buffer), language="bash")

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

        full_log_str = "\n".join(full_log_content) if full_log_content else ""
        return full_log_str, result_status

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
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

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
            if current_root_str.endswith("/src") or "/externs/" in current_root_str or current_root_str.endswith("/externs"):
                continue

            for file in files:
                # 扩展名过滤
                if any(file.endswith(ext) for ext in IGNORED_EXTENSIONS):
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

        # 2. 文件层设计：下拉选择 + 内容展示
        for idx, tab_name in enumerate(tab_names_list):
            dir_path = tabs_map[tab_name]

            with dir_tabs[idx]:
                dir_files = sorted(result_dirs_map[dir_path])
                files_with_names = list(zip([f.name for f in dir_files], dir_files))
                files_with_names.sort(
                    key=lambda item: (
                        item[0].endswith("indexing") or ".indexing" in item[0],
                        item[0],
                    )
                )
                file_names = [name for name, _ in files_with_names]
                dir_files = [path for _, path in files_with_names]

                # 文件选择组件
                select_key = f"selected_file_{tab_name}"
                if select_key not in st.session_state:
                    st.session_state[select_key] = None
                
                selected_file = st.selectbox(
                    "选择文件",
                    options=file_names,
                    index=None,
                    placeholder="Choose options",
                    key=f"select_{tab_name}",
                    label_visibility="collapsed",
                )
                
                if selected_file:
                    selected_idx = file_names.index(selected_file)
                    st.session_state[select_key] = str(dir_files[selected_idx])
                
                if st.session_state[select_key] is None:
                    continue
                
                file_path = Path(st.session_state[select_key])

                st.markdown(f"**文件路径**: `{file_path}`")

                with st.spinner(f"正在加载 {file_path.name} ({file_path.suffix.upper()})..."):
                    if file_path.suffix.lower() not in TXT_EXTENSIONS:
                        try:
                            df = self.read_dataframe(file_path)
                            self.render_dataframe_with_search(df, f"{tab_name}_{file_path.name}")
                        except Exception as e:
                            st.warning("尝试作为文本显示...")
                            self.display_as_text(file_path)

                    else:
                        self.display_as_text(file_path)


# --- 主界面逻辑 ---
def main():

    render = Render()
    render.config_logo()

    if LOGO_PATH:
        with open(LOGO_PATH, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        header_html = f"""
        <div style=\"display:flex;align-items:center;gap:12px;margin-bottom:1rem;\">
            <img src=\"data:image/png;base64,{img_b64}\" style=\"height:48px;\" />
            <h1 style=\"margin:0;\">莲花代码分析 (LIAN)</h1>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    else:
        st.title("莲花代码分析 (LIAN)")

    render.build_sidebar()

    # 初始化日志状态
    if "last_cmd" not in st.session_state:
        st.session_state.last_cmd = None
        st.session_state.last_log = None
        st.session_state.last_status = None

    # 执行按钮
    if st.button("开始分析", type="primary", use_container_width=True):
        cmd_list = render.build_command()
        st.session_state.last_cmd = " ".join(cmd_list)
        st.code(st.session_state.last_cmd, language="bash")
        st.subheader("执行日志")
        # 执行并保存日志
        log_result, status = render.create_log_container_with_result()
        st.session_state.last_log = log_result
        st.session_state.last_status = status
    
    # 显示上次执行的日志（如果有）
    elif st.session_state.last_cmd:
        st.code(st.session_state.last_cmd, language="bash")
        st.subheader("执行日志")
        if st.session_state.last_status == "success":
            st.success("✅ 分析完成！")
        elif st.session_state.last_status == "error":
            st.error("❌ 分析异常终止")
        if st.session_state.last_log:
            with st.expander("点击查看控制台输出", expanded=False):
                st.code(st.session_state.last_log, language="bash")

    st.subheader("分析结果可视化")
    render.render_results()

if __name__ == "__main__":
    main()
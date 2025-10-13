# import streamlit as st
# import pandas as pd
# import numpy as np  # 用于示例数据生成

# # 设置页面标题
# # st.title('DataFrame 数据网页展示 [1,6](@ref)')
# # st.header('员工信息表')

# # # 创建示例DataFrame [1](@ref)
# data = {
#     '姓名': ['张三', '李四', '王五', '赵六', '钱七'],
#     '年龄': [25, 32, 28, 41, 36],
#     '城市': ['北京', '上海', '广州', '深圳', '杭州'],
#     '薪资': [15000, 22000, 18000, 35000, 28000]
# }
# df_uploaded = pd.DataFrame(data)

# # uploaded_file = st.file_uploader("/home/corgi/project/hm-tests/harmony_analysis/test/analyzer_workspace/lian_workspace/basic/gir.indexing")
# # if uploaded_file is not None:
# df_uploaded = pd.read_feather("/home/corgi/project/hm-tests/harmony_analysis/test/analyzer_workspace/lian_workspace/basic/gir.bundle0")
# st.dataframe(df_uploaded)


# 显示DataFrame [3](@ref)
# st.subheader('使用 st.dataframe 展示 (交互式)')
# st.dataframe(df_uploaded)  # 可排序、搜索、滚动 [3](@ref)

# st.subheader('使用 st.table 展示 (静态)')
# st.table(df_uploaded)  # 静态展示所有数据 [3](@ref)

# # 添加一些交互控件来过滤数据 [1,6](@ref)
# st.sidebar.header("数据筛选")
# selected_city = st.sidebar.selectbox('选择城市', options=['所有'] + list(df['城市'].unique()))
# min_salary = st.sidebar.slider('最低薪资', min_value=int(df['薪资'].min()), max_value=int(df['薪资'].max()), value=15000)

# # 根据筛选条件过滤数据
# if selected_city != '所有':
#     filtered_df = df[(df['城市'] == selected_city) & (df['薪资'] >= min_salary)]
# else:
#     filtered_df = df[df['薪资'] >= min_salary]

# st.subheader('筛选后的数据')
# st.dataframe(filtered_df)

# # 添加一个简单的图表可视化 [6](@ref)
# st.subheader('薪资可视化')
# st.bar_chart(filtered_df.set_index('姓名')['薪资'])

import streamlit as st
import pandas as pd
import pyarrow as pa  # 确保已安装pyarrow

# 设置页面配置
st.set_page_config(
    page_title="Feather文件查看器",
    page_icon="📊",
    layout="wide"
)

# 应用标题
st.title("📊 Feather文件查看器")
st.markdown("使用侧边栏切换不同的Feather文件数据集")

# 初始化session_state，用于存储当前选中的文件
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

# 在侧边栏中添加文件选择器
with st.sidebar:
    st.header("🗂️ 文件选择")

    # 使用radio按钮让用户选择要查看的文件
    file_option = st.radio(
        "选择要查看的Feather文件:",
        options=["gir", "s2space_p3", "s2space_p2", "cfg", "call_path_p3", "stmt_status_p2"],
        help="选择您想要查看的数据集"
    )

    st.markdown("---")
    st.info("选择上面的选项来切换不同的数据集")


# 根据用户选择加载相应的Feather文件
def load_feather_file(file_choice):
    """根据选择加载Feather文件"""
    try:
        if file_choice == "gir":
            # 替换为你的第一个feather文件路径
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/basic/gir.bundle0")
            st.session_state.current_file = "gir"
        elif file_choice == "s2space_p3":
            # 替换为你的第二个feather文件路径
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/semantic_p3/s2space_p3.bundle0")
            st.session_state.current_file = "s2space_p3"
        elif file_choice == "s2space_p2":
            # 替换为你的第二个feather文件路径
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/semantic_p2/s2space_p2.bundle0")
            st.session_state.current_file = "s2space_p2"
        elif file_choice == "cfg":
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/basic/cfg.bundle0")
            st.session_state.current_file = "cfg"
        elif file_choice == "call_path_p3":
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/semantic_p3/call_path_p3")
            st.session_state.current_file = "call_path_p3"
        elif file_choice == "stmt_status_p2":
            df = pd.read_feather(
                "/home/corgi/workspace/lian/lian/tests/lian_workspace/semantic_p2/stmt_status_p2.bundle0")
            st.session_state.current_file = "stmt_status_p2"
        return df
    except Exception as e:
        st.error(f"读取文件时出错: {e}")
        return None


# 加载选中的文件
current_df = load_feather_file(file_option)

if current_df is not None:
    # 显示文件信息和数据预览
    st.header(f"📋 当前查看: {st.session_state.current_file}")

    # 创建列布局显示基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("行数", current_df.shape[0])
    with col2:
        st.metric("列数", current_df.shape[1])
    with col3:
        st.metric("文件", st.session_state.current_file)

    # 显示数据预览
    st.subheader("数据预览")
    st.dataframe(current_df, use_container_width=True)

    # 显示列信息
    with st.expander("📝 查看列信息"):
        col_info = pd.DataFrame({
            '列名': current_df.columns,
            '数据类型': current_df.dtypes.values,
            '非空值数量': current_df.count().values
        })
        st.table(col_info)

    # 显示基本统计信息（仅数值列）
    numeric_cols = current_df.select_dtypes(include=['number']).columns
    if not numeric_cols.empty:
        with st.expander("📈 数值列统计信息"):
            st.write(current_df[numeric_cols].describe())
    else:
        st.info("当前数据集没有数值列可供统计")
else:
    st.warning("请确保Feather文件路径正确，并且已安装pyarrow库")

# 添加使用说明
with st.sidebar:
    st.markdown("---")
    st.subheader("使用说明")
    st.markdown("""
    1. 在侧边栏选择要查看的文件
    2. 主区域将显示选中的数据集
    3. 可以查看数据预览、列信息和统计摘要
    4. 确保文件路径正确且已安装pyarrow
    """)

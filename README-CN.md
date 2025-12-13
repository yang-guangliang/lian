## 新一代程序分析框架：莲花（Lian）

“莲花”Lian是新一代的程序分析框架，采用“多语言统一”的设计理念，将所支持的语言统一转换为通用中间表示GIR（General Intermediate Representation），并在此基础上进行统一的语义分析与安全检测。只需为新语言适配轻量级前端，即可快速实现上下文敏感、流敏感的指针级代码分析能力。

Lian框架包含三大核心模块：

- **基于GIR语言前端**：与LLVM等传统中间语言不同，GIR支持对有类型与无类型语言的统一表达

- **语义分析引擎**：基于GIR构建上下文敏感、流敏感的指针级语义模型，并输出状态流图SFG（State Flow Graph）作为程序语义的结构化表示

- **污点分析模块**：在SFG上识别敏感源（source）与汇聚点（sink），高效追踪从source到sink的数据流路径，支撑漏洞检测、隐私泄露分析等安全任务

## 安装和使用

### 当前运行环境要求：
- Linux
- Python 3+

### 安装步骤：
1. 下载最新的Lian代码：
```shell
$ git clone https://gitee.com/fdu-ssr/lian.git
````

或者从[发行版](https://gitee.com/fdu-ssr/lian/releases)页面下载稳定版本。

2. 安装依赖库：

```shell
# 进入Lian仓库
$ cd lian
# 安装Python依赖库
$ pip install -r requirements.txt
```

### 启动可视化工具：

Lian提供了可视化工具，运行以下命令启动：

```shell
$ ./scripts/lian-ui.sh
```

### 使用命令行工具：

Lian还提供了命令行工具，支持直接分析代码：

```shell
$ ./scripts/lian.sh -l <语言> <待分析代码路径>
```

## 文档和支持

更多技术细节，请参考[Wiki（中文文档）](https://gitee.com/fdu-ssr/lian/wikis/pages)。欢迎通过[Issue](https://gitee.com/fdu-ssr/lian/issues)提交反馈和建议！

## 关于我们

Lian由复旦大学[FUDAN-SSR（System Security and Reliability）](https://gitee.com/fdu-ssr)研究组自主研发。我们致力于构建可扩展、高精度、多语言的程序分析基础设施。
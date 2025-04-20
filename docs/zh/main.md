莲花Lian系统是新一代计算机语言分析框架，支持多种编程语言的深度语义分析，支持各类AI任务和代码安全分析。莲花系统通过将各种计算机语言转化为自研的通用性语言GLang，支持对各类静态语言（如C/C++，Java，TypeScript，ArkTS，Rust，Go等）和动态语言（如Python，JavaScript，Ruby等）的分析，以及跨语言的代码分析。莲花系统能够深度分析程序状态，高精度分析程序控制流、调用图、数据流和污点跟踪等。

同时，莲花系统高度自动化、可定制化和可扩展化，支持AI用户一键提取程序语义信息，实现与各类AI系统无缝衔接，同时支持程序分析人员自定义分析插件，检测和插装、修改程序分析逻辑。

莲花系统是开源和开放的，采用的是Apache2.0开放协议，欢迎创建PR和提交Issue。
欢迎引用我们的工作
```bibtex
@article{Lian,
  title={Lian: A Universal Language Analysis Framework for AI and Security},
  author={xxx},
  journal={xxx},
  year={2023}
}
```


## 安装和快速运行

```bash
pip install liansec
```
既可以通过命令行直接运行莲花，
```bash
lian.sh ...
```

也可以通过接口调用的方式（如污点跟踪）：
```python
from lian.interfaces.command import Lian

Lian.taint_analyze(program_path, output_path, taint_config_path)
```

## 系统设计

Lian主要包括以下几个模块：
 - lang语言分析：把计算机语言转换成我们自己设计的中间语言GLang
 - semantic语义分析：基于该中间语言，进行深度语义分析，包括控制流、跨函数级数据流、程序状态计算等
 - security安全分析：通过污点跟踪，进行安全验证

### lang语言分析

不同的计算机语言存在迥异的语法。为了承载大部分计算机语言的语言规则，我们设计一种通用性的中间语言GLang（General Language）已达成表示语言的作用。

### Semantic语义分析

语义分析不仅要容纳于c、java等有类型语言，还需要处理JavaScript、Python等无类型语言。这需要包含两个层次的分析：一个是symbol符号级别的分析，另一个是state计算机状态级别的分析。符号级别分析主要是传统的分析，包括控制流图control flow graph、控制流data flow graph、基础调用图basic call graph。但是传统符号级别分析无法解决无类型语言的分析，因此需要启动状态分析。

语义分析可以分为三个层次的分析：
- 基础分析basic analysis：主要做scope分析、入口分析、以及flow-insensitive级别def-use分析
- 状态计算state compute
    - 从下而上分析bottomup analysis：主要做基于模版（摘要）的分析
    - 从上而下分析topdown analysis：主要做基于现实状态的分析

### Security安全分析



## Lian: Next-Generation Program Analysis Framework

"Lian" is a next-generation program analysis framework. Lian applies the "all-in-one" design philosophy, converting languages into General Intermediate Representation (GIR) for unified semantic analysis and security detection. By simply adapting a lightweight frontend for a language (~1,600 lines of code), one can achieve deep code analysis.

The Lian framework consists of three core modules:

- **GIR-based Language Frontend**: Unlike traditional IR like LLVM, GIR supports the unified representation of both typed and untyped languages.

- **Semantic Analysis Engine**: Lian constructs context- and flow-sensitive points-to and data-flow analysis, and outputs SFG (State Flow Graph) as a structured representation of program semantics.

- **Taint Analysis**: On top of SFG, Lian automatically identifies sensitive sources and sinks and efficiently tracks data flow paths, supporting security tasks such as vulnerability detection and privacy leakage analysis.

## Installation and Usage

### System Requirements:
- Linux
- Python 3+

### Installation:
1. Clone the latest Lian repository:
```shell
$ git clone git@gitee.com:fdu-ssr/lian.git
````

Alternatively, a stable version is available in [Release](https://github.com/yang-guangliang/lian/releases).

2. Install the dependencies:

```shell
# Enter the Lian directory
$ cd lian
# Install Python dependencies
$ pip install -r requirements.txt
```

### Launch the Visualization Tool:

Lian provides a visualization tool for easier usage:

```shell
$ ./scripts/lian-ui.sh
```

### Using the Command-Line Tool:

Lian also provides a command-line tool for direct code analysis:

```shell
$ ./scripts/lian.sh -l <language> <path_to_code_to_analyze>
```

## Documentation and Support

For more technical details, please refer to [Documentation](https://yang-guangliang.github.io/lian/en).

Feel free to submit feedback and suggestions via [Issues](https://github.com/yang-guangliang/lian/issues),[Discussions](https://github.com/yang-guangliang/lian/discussions), and [Pull Requests](https://github.com/yang-guangliang/lian/pulls)!


## About Us

Lian is independently developed by the [FDU-SSR (System Security and Reliability)](https://yang-guangliang.github.io/) research group at Fudan University. We are committed to building a scalable, high-precision, and multiple-language program security analysis infrastructure.




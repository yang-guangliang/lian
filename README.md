# The Lian Program Analysis Framework

**Lian** is a next-generation, high-precision program analysis framework designed for multi-language environments. It aims to deliver unified and powerful program analysis capabilities across diverse programming languages, including pointer analysis, dataflow analysis, and taint analysis.

## Background

<<<<<<< HEAD
Program analysis is a foundational technology in system security. The prior program analysis tools designed for mainstream statically typed languages (such as C/C++ and Java) are already highly mature and robust. However, in today's diverse programming language ecosystem, high-precision program analysis capabilities remain severely lacking, significantly hindering the analysis and enhancement of software security and reliability.

In past, many programming languages have become extremely popular:
=======
In past, many languages are becomming increasingly popular, especially dynamically typed languages. Python dominates AI and data engineering, JavaScript and TypeScript power web and cross-platform applications and frameworks, and Go and Rust greatly boosts cloud service and systems programming. These languages significantly improve developer productivity, but there are also many highly dynamic runtime semantics breaking the assumptions that traditional static analysis techniques rely on.

In many causes, type information is often unavailable or unstable, object layouts evolve at runtime, and control flow depends on dynamic dispatch, higher-order functions and reflective property access. As a result, conventional static analyses (originally designed for statically typed and single-language systems) struggle to maintain both precision and scalability on real-world dynamic codebases. They either over-approximate aggressively and lose precision, or become computationally intractable.
>>>>>>> aec4bc7 (update readme)

- **Python** dominates artificial intelligence and data engineering;
- **TypeScript** became the #1 most-used language on GitHub in 2025. jointly with **JavaScript**, they power web and cross-platform application development;
- **Go** and **Rust** play critical roles in cloud services and systems programming.

Yet, traditional analysis tools still struggle to support these languages effectively:

<<<<<<< HEAD
- **Tight language binding**: Analysis logic is deeply coupled with the syntax and type systems of specific languages (e.g., C/C++, Java). Supporting a new language often requires rebuilding the entire system from scratch.
- **Failure under dynamic behavior**: Analysis algorithms heavily rely on stable object layouts and explicit type declarations. When analyzing untyped code or programs with dynamically evolving object structures, they either produce overly coarse approximations or suffer from state explosion.

## Unified Program Analysis
=======
Different from traditional analyses that assume stable object models and reliable type constraints, Lian takes a different path. It abstracts program behavior into a set of language-agnostic semantic primitives and performs analysis directly at this level, instead of anchoring analysis logic to surface-level syntax or type systems.
>>>>>>> aec4bc7 (update readme)

Despite vast syntactic differences across languages, program behaviors at the execution level can all be reduced to a common set of semantic operations, enabling unified analysis.

- **Generic Intermediate Representation (GIR)**: A concise and universal IR that supports both statically and dynamically typed languages. Translating any source language into GIR requires only ~1,600 lines of code.
  
- **Unified Analysis Engine**: High-precision pointer analysis, dataflow analysis, and taint analysis are implemented atop GIR. 

- **Support Inconsistency**: The framework provides an extensible plugin architecture to support custom analyses and be compatible with the features in various languages.

## Key Features

* **Source-code input**: Analyzing source code directly. No compiler is required.  
* **Multi-language support**: Supporting both static and dynamic languages, including Python, JavaScript, Java, TypeScript, and Go.  
* **Pointer-level precision**: Implementing flow-sensitive and context-sensitive pointer analysis.  
* **Dynamic semantics modeling**: Accurately handling prototype chains, higher-order functions, and dynamic property resolution.  
* **Security-oriented**: Providing a powerful taint analysis engine, enabling rapid development of vulnerability discovery tools.

## Usage

### System Requirements

<<<<<<< HEAD
* Linux environment  
* Python 3.10+
=======
Lian currently targets Unix-like environments and requires Python 3.10 or above.
>>>>>>> aec4bc7 (update readme)

### Download and Install

Clone the repository:

```shell
$ git clone https://github.com/yang-guangliang/lian.git
$ cd lian
```

Install dependencies:

```shell
$ pip install -r requirements.txt
```

### Running Lian

Lian supports both a graphical user interface and command-line mode:

**1. Launching the visual analysis tool:**

```shell
$ ./scripts/lian-ui.sh
```

<kbd>![](docs/cn/img/lian-ui.png)</kbd>

**2. Performing analysis via command line:**

```shell
$ ./scripts/lian.sh -l <language> <path_to_code>
```

## Documentation and Support

For more technical details, please refer to [Documentation](https://yang-guangliang.github.io/lian/en). Also, we provide [Lecture Notes on Program Analysis](https://yang-guangliang.github.io/lian/en/02.background/2-1.basics/) (covering fundamentals, dataflow analysis, pointer analysis, and taint analysis), as a reference.

Feel free to submit feedback and suggestions via [Issues](https://github.com/yang-guangliang/lian/issues),[Discussions](https://github.com/yang-guangliang/lian/discussions), and [Pull Requests](https://github.com/yang-guangliang/lian/pulls)!

## Project Status

Lian is an active and research-driven project. Lian is independently developed by the [SSR (System Security and Reliability) research group](https://yang-guangliang.github.io/) at Fudan University. We are committed to building a generic, scalable, and high-precision program security analysis infrastructure.


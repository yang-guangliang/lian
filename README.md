# Lian

Lian is a unified pointer-level program analysis framework for supporting multiple languages. It is designed to provide a reusable analysis foundation for pointer analysis, context-sensitive dataflow analysis, and security-oriented reasoning.

## Overview

In past, many languages are becomming increasingly popular, especially dynamically typed languages. Python dominates AI and data engineering, JavaScript and TypeScript power web and cross-platform applications and frameworks, and Go and Rust greatly boosts cloud service and systems programming. These languages significantly improve developer productivity, but there are also many highly dynamic runtime semantics breaking the assumptions that traditional static analysis techniques rely on.

In many causes, type information is often unavailable or unstable, object layouts evolve at runtime, and control flow depends on dynamic dispatch, higher-order functions and reflective property access. As a result, conventional static analyses (originally designed for statically typed and single-language systems) struggle to maintain both precision and scalability on real-world dynamic codebases. They either over-approximate aggressively and lose precision, or become computationally intractable.

### Mean Idea

Lian is built on the observation that the fundamental limitation of existing approaches is not insufficient language-specific modeling, but the lack of a **unified** semantic foundation that remains valid across dynamic behavior and language boundaries.

Different from traditional analyses that assume stable object models and reliable type constraints, Lian takes a different path. It abstracts program behavior into a set of language-agnostic semantic primitives and performs analysis directly at this level, instead of anchoring analysis logic to surface-level syntax or type systems.

### Design Philosophy

Lian adopts a language-agnostic design by reducing program behavior to fundamental semantic operations such as object creation, reference propagation, property access, and dynamic call resolution.

Programs written in different languages are translated into a generic intermediate representation (GIR) that makes these operations explicit. The analysis core operates solely on this representation, ensuring that pointer-level reasoning and dataflow semantics have a consistent interpretation across languages.

Language-specific complexity is isolated in frontend translations, while the analysis engine itself remains uniform. This separation allows Lian to evolve as new languages, execution models, and security analyses are added, without re-engineering the analysis core.

### How Lian Differs from Existing Frameworks

Most existing program analysis frameworks are language-centric. Their analysis logic is tightly coupled to constructs such as types, classes, or declared fields, which works well within a single language ecosystem but limits reuse across languages and breaks down in highly dynamic settings.

Lian shifts the abstraction boundary. Instead of treating language syntax as the foundation of analysis, it treats runtime semantics as the common ground. Language constructs become artifacts of frontend translation, not fundamental elements of the analysis itself.

Lian is not intended to replace traditional frameworks in the domains where they excel. Rather, it provides a shared analytical foundation for polyglot systems, dynamic execution environments, and security reasoning scenarios where language-centric tools reach their limits.

## Installation and Usage

### System Requirements

Lian currently targets Unix-like environments and requires Python 3.10 or above.

### Installation

Clone the latest version of the Lian repository:

```shell
$ git clone https://github.com/yang-guangliang/lian.git
$ cd lian
````

Alternatively, a stable version can be obtained from the GitHub Releases page.

Install the required Python dependencies:

```shell
$ pip install -r requirements.txt
```

### Running Lian

Lian can be used either through a visualization interface or via the command line.

To launch the visualization tool:

```shell
$ ./scripts/lian-ui.sh
```

For direct analysis from the command line:

```shell
$ ./scripts/lian.sh -l <language> <path_to_code_to_analyze>
```

## Documentation and Support

For more technical details, please refer to [Documentation](https://yang-guangliang.github.io/lian/en).

Feel free to submit feedback and suggestions via [Issues](https://github.com/yang-guangliang/lian/issues),[Discussions](https://github.com/yang-guangliang/lian/discussions), and [Pull Requests](https://github.com/yang-guangliang/lian/pulls)!

## Project Status

Lian is an active and research-driven project. Lian is independently developed by the [SSR (System Security and Reliability) research group](https://yang-guangliang.github.io/) at Fudan University. We are committed to building a generic, scalable, and high-precision program security analysis infrastructure.


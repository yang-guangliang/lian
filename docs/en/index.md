# **Why LIAN?**

Static analysis is a critical method for understanding software code behavior and identifying potential security risks. In recent years, with the exponential growth of codebases, the widespread adoption of multi-language heterogeneous programming, and dynamic syntax features, software behavior has become increasingly diverse and complex, posing significant challenges for static analysis. This issue is particularly pronounced when analyzing dynamic languages. Existing static analysis tools often prioritize maintaining the soundness of analysis results, leading to excessive approximations and severe precision issues — valuable security findings are often buried in a flood of irrelevant results, severely undermining the practicality of these tools. Some tools attempt to enhance static analysis by incorporating dynamic runtime results, but the limited coverage of dynamic analysis restricts this enhancement. Therefore, improving the precision of static analysis remains an urgent challenge in software security.

# **LIAN System Intro**

To address this challenge, we have developed LIAN Lotus System, a high-precision universal software security analysis platform. By simulating runtime states through abstract interpretation while maintaining the broad coverage of static analysis, LIAN enables precise software security analysis. Key features include:

- End-to-end one-click execution: No complex environment setup or source code modification is required. Users simply specify the target directory/file, and LIAN generates analysis results such as call graphs, control flow graphs, and program state spaces, with optional visualization. It supports both complete programs and library code.

- Multi-language support: Compatible with static languages (e.g., Java, C) and dynamic languages (e.g., Python, JavaScript, PHP), as well as mobile bytecode (e.g., Android Dalvik) and intermediate languages (e.g., LLVM).

- Unified intermediate representation ([GIR](gir.md)): LIAN's language frontends convert diverse languages into the Generic Intermediate Representation (GIR) for high-precision semantic analysis.

- Semantic analysis capabilities:

  - Type hierarchy analysis

  - File dependency analysis

  - Control flow analysis

  - Cross-function data flow analysis

- Advanced state computation: Implements context-sensitive, flow-sensitive, field-sensitive, and path-sensitive runtime state tracking to support analyses like taint tracking and call graph construction.

- Result storage: Intermediate and final results are stored in a database for easy querying and utilization.

- Extensible infrastructure:

  - Event-based plugin system for customization

  - Memory and file management to prevent memory explosion


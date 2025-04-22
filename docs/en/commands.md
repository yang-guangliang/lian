# **Command-Line Parameter Configuration**

This page documents the command-line parameter configuration for Lian, divided into **Input Parameters** and **Output Parameters** below.

## Input Parameters

| Parameter | Synonym      | Description                          | Example                            |
| ---- | ------------- | ----------------------------- | ------------------------------- |
| -d   | --debug       | Enable the DEBUG mode | .\lian.sh -d <target.py>        |
| -p   | --print_stmts | Print statements                   | .\lian.sh -p <target.py>        |
| -l   | --lang        | programming lang              | .\lian.sh -l python <target.py> |

## Output Parameters

| Parameter | Synonym    | Description                                     | Example                              |
| ---- | ----------- | ---------------------------------------- | --------------------------------- |
| -w   | --workspace | the workspace directory (default:lian_workspace) | .\lian.sh <target.py> -w .\output |
| -f   | --force     | Enable the FORCE mode for rewritting the workspace directory                 | .\lian.sh <target.py> -f          |

Notes:
Parameter names (e.g., -d, --debug) are formatted as inline code.

Examples retain their original command syntax and placeholders (e.g., <target.py>).

Formatting (headers, tables, emphasis) strictly follows the original structure.
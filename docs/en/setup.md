# **Install & Run**

1、Environment required：Linux  +  Python3；

2. Download LIAN repository：

```shell
git clone https://gitee.com/fdu-ssr/lian.git
```

3. Install the requirements of python：

```shell
cd lian                  
pip install -r requirements.txt     
```

4. Basic use：

```shell
./scripts/lian.sh -l <language> <filepath>
```

# **Command-Line Parameter Configuration**

LIAN's command-line options include

| Parameter | Synonym      | Description                          | Example                            |
| ---- | ------------- | ----------------------------- | ------------------------------- |
| -d   | --debug       | Enable the DEBUG mode | .\lian.sh -d <target.py>        |
| -p   | --print_stmts | Print statements                   | .\lian.sh -p <target.py>        |
| -l   | --lang        | programming lang              | .\lian.sh -l python <target.py> |
| -w   | --workspace | the workspace directory (default:lian_workspace) | .\lian.sh <target.py> -w .\output |
| -f   | --force     | Enable the FORCE mode for rewritting the workspace directory                 | .\lian.sh <target.py> -f          |


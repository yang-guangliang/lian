# **安装并运行**

1、当前环境要求：Linux  +  Python3；

2、下载LIAN仓库：

```shell
git clone https://gitee.com/fdu-ssr/lian.git
```

3、安装python依赖库：

```shell
cd lian                  
pip install -r requirements.txt     
```

4、lian的基础使用：

```shell
./scripts/lian.sh -l <语言> <待分析代码文件路径>
```

注：1、待分析代码文件路径可以是绝对路径或者是相对路径

​    2、对于 `.\lian.sh` 命令行参数的配置可以参考[命令行参数配置](./commands.md)


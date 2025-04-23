# 简单例子
```
# example.py
def callee(a):
    b = a["x"]
    #vulnerable_function
    b["func"] = lambda x : print("vulnerable")
    
o = {
    "x" : {}
}

def caller():
    p = o["x"]
    # benign_function
    p["func"] = lambda x : print("benign")
    callee(o)
    target = p["func"]
    target()

caller()
```

# 使用LIAN分析
```
scripts/test.sh <example.py> #仅限测试
```
----
# 运行截图
![输入图片说明](../img/Snipaste_2025-04-23_16-14-07.png)
![输入图片说明](../img/image%20(1).png)

----
# GIR结果
## callee函数定义
![输入图片说明](../img/image%20(2).png)
## caller函数定义
![输入图片说明](../img/image%20(3).png)
## %unit_init函数定义
![输入图片说明](../img/image%20(4).png)
----
# 结果解读
&emsp;从GIR表(gir.bundle0)中可以看出，call target()是第55条GIR_stmt。<br>
![输入图片说明](../img/image%20(5).png)<br>
&emsp;运行LIAN后，生成该程序的状态空间(s2space_p3.bundle0)。从状态空间中能够看到第55条GIR_stmt中，target变量中的状态index为61。<br>
![输入图片说明](../img/image%20(6).png)
&emsp;查阅状态空间(s2space_p3.bundle0)找到index为61的状态，可以看到其data_type为一个方法声明，则其value值27表示该方法声明的GIR_stmt_id。<br>
![输入图片说明](../img/image%20(7).png)
&emsp;查阅GIR(gir.bundle0)，发现第27条GIR_stmt对应着恶意方法%mm1。说明该状态成功被计算出来。<br>
![输入图片说明](../img/image%20(8).png)

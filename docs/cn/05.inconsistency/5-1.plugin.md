## **插件系统（event_manager）**

&emsp;不同语言的独特的特性需要具体情况具体分析处理，例如javascript语言的原型链，为了使分析工具具备可扩展性，本工具加入插件系统。当开发者需要添加一个新插件时，首先在app_register.py与event_manager.py中注册插件，并准备好插件的处理代码，然后在合适的位置准备好插件的输入并通过EventManager.notify()触发插件，当插件被触发后，返回插件的输出结果以及插件的处理情况。<br>
&emsp;以处理javascript的原型链的插件为例，开发人员注册完并准备好插件的处理代码后，在合适的位置触发插件:

```python
...
event = EventData(
            #该插件生效的语言
            self.lang,
            #插件调用的阶段
            EventKind.P2STATE_NEW_OBJECT_BEFORE,
            {
            #插件的输入数据
                "stmt_id": stmt_id,
                ...
            }
        )
#触发插件,并返回插件的输出结果以及插件的处理情况
app_return = self.event_manager.notify(event)
#根据插件的处理情况决定后续的分析
if event_return.is_event_unprocessed(app_return):
    ...

```
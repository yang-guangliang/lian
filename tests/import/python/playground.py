"""
@desc: 该文件用于让大模型决定需要哪些函数的源代码
"""
from openai import OpenAI
import ast


class SourceCodeSession:
    def __init__(self, method_list):
        """
        这里的method_list应该是LIAN中loader得到的summary_generation.analyzed_method_list处理后得到的{'method_name': 'method_id'}
        类型为dict
        """
        prompt = self.generate_system_prompt(method_list)
        print(prompt)
        self.init_session(prompt)

    def init_session(self, system_prompt):
        self.client = OpenAI(
            api_key = "sk-axjlyvarytvxwbqwcxdwfbuopbahbmiplywisyziiqtihmzc",
            base_url="https://api.siliconflow.cn/v1/"
        )
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]


    def generate_system_prompt(self, method_list):
        system_prompt = """
        我会给你一个json格式文件，键是函数名称，值是函数的id。对于每个函数，如果你没有在聊天的上下文中找到定义，就加入到返回结果中
        如果一个都没有找到，就返回原json文件，如果都找到了，就返回空的json文件
        输入json文件为：""" + str(method_list) + """
        - 输出一定是一个json格式：
        {
            "函数名": 函数id,
            ...
        }
        注意：不要有多余的输出，只要一个json就行了
        """
        return system_prompt

    def chat(self, user_input):
        # 添加用户消息到上下文
        content = f"现在我给你以下源代码，你继续返回没有找到定义的函数: \n{user_input}"
        self.messages.append({"role": "user", "content": "" + content})
        print(f"👶: {content}")

        try:
            response = self.client.chat.completions.create(
                model="THUDM/GLM-4.1V-9B-Thinking",  # 指定要使用的模型，可以根据需要更换
                messages=self.messages,
                stream=False,          # 设置为False以获取完整回复，True则为流式输出
                max_tokens=512,        # 设置生成文本的最大token数
                temperature=0.7        # 设置生成文本的随机性
                # 可以根据API文档添加更多参数，如 top_p, frequency_penalty 等
            )

            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})

            print(f'🤖️: {reply}')
            self._print_usage(response.usage)

            return reply
        
        except Exception as e:
            print(f"API错误：{e}")
            return None
        
    def _print_usage(self, usage):
        print(f"\nToken使用: 输入={usage.prompt_tokens} 输出={usage.completion_tokens} 总计={usage.total_tokens}")


def test():
    session = SourceCodeSession({'__init__': 24, 'main': 131, 'chat': 36, 'generate_system_prompt': 107, 'generate_user_prompt': 112, '_print_usage': 82, '%unit_init': 148})
    # chat函数的输入应该是loader读取的源代码处理后的一整个字符串
    source_code = """
    def __init__(self, system_prompt):
        self.client = OpenAI(
            api_key = "sk-axjlyvarytvxwbqwcxdwfbuopbahbmiplywisyziiqtihmzc",
            base_url="https://api.siliconflow.cn/v1/"
        )
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]
        
    def _print_usage(self, usage):
        print(f"\\nToken使用: 输入={usage.prompt_tokens} 输出={usage.completion_tokens} 总计={usage.total_tokens}")
    """
    reply = ast.literal_eval(session.chat("空"))
    # 对大模型的回复进行处理，给到loader以获取没有源代码的函数
    tmp = "未找到的函数的id："
    for idx in reply.values():
        tmp += str(idx) + ", "
    print(tmp)


test()

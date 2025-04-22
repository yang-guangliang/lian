
def static_vars(**kwargs):
    """
    [rn]
    作用：给一个函数添加一个静态变量，每次调用该方法时都引用相同的值或对象。
    """
    def decorate(func):
        for k, v in kwargs.items():
            # 创建一个新的实例，避免共享状态。若希望创建一个静态set，每次装饰新函数时都会创建一个新set实例，而不是共享同一个实例。
            value = v() if callable(v) else v
            setattr(func,k,value) 
        return func
    return decorate
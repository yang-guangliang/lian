// 只读属性
public int Age { get; }

// 可读写属性
public string Name { get; set; }

// 只写属性（不常见，但可以定义）
public string Secret { set { /* 逻辑处理 */ } }

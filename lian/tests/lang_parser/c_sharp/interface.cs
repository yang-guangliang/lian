// interface类型
public interface MyShape : Shape
{    
    // 方法声明
    void Draw();

    ~IShape()
}

// record类型
public record Person(FirstName FirstName, LastName LastName);

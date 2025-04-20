// public静态类定义
public static class Person
{
    ~Person();

    public string Name { get; set; }
    public int Age { get; set; }


    
    public Person(string name, int age)
    {
        Name = name;
        Age = age;
    }
    
    public void DisplayInfo()
    {
        Console.WriteLine($"Name: {Name}, Age: {Age}");
    } 
}

// 继承类
public class Student : Person
{
    public string School { get; set; }
    
    public Student(string name, int age, string school) : base(name, age)
    {
        School = school;
    }
    
    public override void DisplayInfo()
    {
        base.DisplayInfo();
        Console.WriteLine($"School: {School}");
    }
}
// 泛型类
public class GenericList<T>
{
    private T[] _items;
    private int _count;

    public GenericList(int capacity)
    {
        _items = new T[capacity];
        _count = 0;
    }

    public void Add(T item)
    {
        _items[_count++] = item;
    }
}
*/
// 嵌套类
public class OuterClass
{
    private int outerField = 10;

    // 非静态嵌套类
    public class InnerClass
    {
        public void PrintOuterField()
        {
            // 直接访问外部类的私有字段
            Console.WriteLine(outerField);
        }
    }
}
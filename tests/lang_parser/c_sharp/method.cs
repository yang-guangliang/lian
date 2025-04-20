public class MethodTest
{

    [Obsolete("This method is obsolete. Use NewMethod instead.")]
    public int AddNumbers<T>(int a=1, int b=0)where a: struct
    {
        return a + b;
    }

}

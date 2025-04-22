public class testtest {
    public void f() {
        System.out.println("test1");
    }
    
    public static void main(String[] args) {
        testtest test = new testtest() {
            public void f() {
                System.out.println("test2");
            }
        };
        test.f();  // 输出 "test2"
    }
}


/* 
class name:%cc0 supers: [testtest] {
    int f() { print "new A"}
}
test = %cc0()

*/
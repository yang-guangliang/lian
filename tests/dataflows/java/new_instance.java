package tests.resource.state_flow.java;

import java.util.ArrayList;
import java.util.HashMap;

// class Person {
//     private String name;
//     private int age;

//     public Person(String name, int age) {
//         this.name = name;
//         this.age = age;
//     }
// }

public class new_instance {
    public static void main(String[] args) {
        String str = new abc("hello");
        ArrayList<Integer> list = new ArrayList<>();
        HashMap<String, Integer> map = new HashMap<>();
        str = "hello";
        String str2 = str + " world";

        Person person = new Person("John", 25);
    }
}
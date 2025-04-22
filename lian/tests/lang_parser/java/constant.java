interface IClassConstants {
    // interface constant
    int NUM_STUDENTS = 100;
}

public class Main {
    // class constant
    public static final int NUM1 = 100;
    public static void main(String[] args) {
        // method constant
        final int NUM2 = 100;
        System.out.println("There are " + NUM2 + " students in this class.");
    }
}
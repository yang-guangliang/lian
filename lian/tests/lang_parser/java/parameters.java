public class VarargsExample {
    public static void printNumbers(int... numbers) {
        for (int number : numbers) {
            System.out.print(number + " ");
        }
    }

    public static void main(String[] args) {
        printNumbers(1, 2, 3, 4);  // 输出: 1 2 3 4 
        printNumbers(5, 6);        // 输出: 5 6
    }
}

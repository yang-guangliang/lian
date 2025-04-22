import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

public class ComplexOperation {

    // private List<Integer> data;

    // public ComplexOperation(List<Integer> initialData) {
    //     this.data = initialData;
    // }

    // public List<Integer> processData(int input) {
    //     return data.stream()
    //             .map(item -> item * input)
    //             .peek(item -> writeToFile(item))
    //             .toList();
    // }

    // private void writeToFile(Integer item) {
    //     try (BufferedWriter writer = new BufferedWriter(new FileWriter("output.txt", true))) {
    //         writer.write(item.toString());
    //         writer.newLine();
    //     } catch (IOException e) {
    //         e.printStackTrace();
    //     }
    // }

    public static void main(String[] args) {
        List<Integer> initialData = Arrays.asList(1, 2, 3, 4, 5);
        ComplexOperation operation = new ComplexOperation(initialData);
        List<Integer> result = operation.processData(10);

        System.out.print("Processed data: ");
        result.forEach(System.out::println);
    }
}
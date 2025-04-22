class test{
    static String a = new String("re"), b = new String("d");

    public enum Color{
        RED(a + b){
            @Override
            public void showColor() {
                System.out.println("my color is red");
            }
        },
        BLUE(){
            @Override
            public void showColor() {
                System.out.println("my color is blue");
            }
        };
        private String color;

        private Color(String color){this.color = color;}

        private Color(){}

        public String getColor(){
            return this.color;
        }

        public abstract void showColor();
        
        
        public enum Grayscale{DARK, Light};
    }
}

// public enum Color implements a, b, c, d {
//     RED("re"+ "d"){
//         @Override
//         public void showColor() {
//             System.out.println("my color is red");
//         }
//     },
//     BLUE(){
//         @Override
//         public void showColor() {
//             System.out.println("my color is blue");
//         }
//     };
//     private String color;

//     private Color(String color){this.color = color;}

//     private Color(){}

//     public String getColor(){
//         return this.color;
//     }

//     public abstract void showColor();
// }

// public class ColorTest {
//     public static void main(String[] args) {

//         Color red = Color.RED;
//         Color blue = Color.valueOf("BLUE");

//         for (Color color : Color.values()) {

//             color.ordinal();
//             System.out.println(color.getColor());
//             color.showColor();
//         }
        
//         switch(blue){
//             case RED:
//                 System.out.println("is red");
//                 break;
//             case BLUE:
//                 System.out.println("is blue");
//                 break;
//         }
//     }
// }


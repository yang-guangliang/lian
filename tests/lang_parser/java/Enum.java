// public class Enum {
    interface Displayable {
        void displayAction();
    }
  
    // constant 直接定义
    enum Level {
      LOW,
      MEDIUM,
      HIGH
    }
    // /*
    // 在enum中，每一个enum constant都可以看作是这个enum的一个具体实例。
    // 类比到class: 
    // Level LOW = new Level();
    // Level MEDIUM = new Level();
    // Level HIGH = new Level();
    // */
  
    // // constant 有参数
    // public enum Day {
    //     SUNDAY(0), MONDAY(1), TUESDAY(2), WEDNESDAY(3),
    //     THURSDAY(4), FRIDAY(5), SATURDAY(6);
  
    //     private final int value;
  
    //     Day(int value) {
    //         this.value = value;
    //     }
  
    //     public int getValue() {
    //         return this.value;
    //     }
    // }
    // /*
    // Day SUNDAY = new Day(0);
    // */
    
    // // // constant 附带了一个行为
    public enum TrafficLight implements Displayable {
        RED {
            @Override
            public void displayAction() {
                System.out.println("Stop!");
            }
        },
        // 出现这种重写行为时，处理成创建了一个新的匿名类
        YELLOW {
            @Override
            public void displayAction() {
                System.out.println("Caution!");
            }
        },
        GREEN {
            @Override
            public void displayAction() {
                System.out.println("Go!");
            }
        };
  
        // 抽象方法
        public abstract void displayAction();
  
        private static int count;
  
        // 静态方法
        public static int getCount() {
            return count;
        }
    }
    
    // public enum TrafficLight {
    //     RED(30, 60),
    //     GREEN(60),
    //     YELLOW(5);
  
    //     private final int duration;
    //     private static int count;
  
    //     // 构造函数
    //     private TrafficLight(int duration) {
    //         this.duration = duration;
    //     }
  
    //     // 方法
    //     public int getDuration() {
    //         return duration;
    //     }
  
    //     // 静态初始化块
    //     static {
    //         count = TrafficLight.values().length;
    //         System.out.println("Total number of traffic light states: " + count);
    //     }
  
    //     // 实例初始化块
    //     {
    //         System.out.println("Initializing " + this.name() + " with duration " + this.duration);
    //     }
  
    //     // 静态方法
    //     public static int getCount() {
    //         return count;
    //     }
  
    //     // 普通方法
    //     public void display() {
    //         System.out.println(this.name() + ": Duration is " + this.duration);
    //     }
    // }
  
    // constant 附带一个有参数的行为
  
    public static void main(String[] args) {
      Level myVar = Level.MEDIUM; 
      System.out.println(myVar);
  
      Day today = Day.THURSDAY;
      System.out.println(today);
  
      TrafficLight light = TrafficLight.RED;
      light.displayAction();
  
  
    }
  // }
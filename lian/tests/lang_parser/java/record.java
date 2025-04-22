import java.time.LocalDate;
import java.util.List;

class Records {

    record R3<T>(int x, T y) {
    }

    record R2() {
        public @interface ClassPreamble {
            String author();
            String date();
            int currentRevision() default 1;
        }
    }

    record R4<T>(int x, T y) implements I1 {

    }
    
}
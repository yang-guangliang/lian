@interface ClassPreamble {
   final int NUM_STUDENTS = 100;
   String date();
   int currentRevision() default 1;
   String lastModified() default "N/A";
   String[] tags() default {};
}

enum LogLevel { INFO, WARN, ERROR}

@interface Log {
    LogLevel level() default LogLevel.INFO;
}

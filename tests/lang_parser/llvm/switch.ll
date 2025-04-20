; #include <stdio.h>

; int main() {
;   int day = 4;
  
;   switch (day) {
;     case 1:
;       printf("Monday");
;       break;
;     case 2:
;       printf("Tuesday");
;       break;
;     case 3:
;       printf("Wednesday");
;       break;
;     case 4:
;       printf("Thursday");
;       break;
;     case 5:
;       printf("Friday");
;       break;
;     case 6:
;       printf("Saturday");
;       break;
;     case 7:
;       printf("Sunday");
;       break;
;   }
    
;   return 0;
; }


@.str = private unnamed_addr constant [7 x i8] c"Monday\00", align 1
@.str.1 = private unnamed_addr constant [8 x i8] c"Tuesday\00", align 1
@.str.2 = private unnamed_addr constant [10 x i8] c"Wednesday\00", align 1
@.str.3 = private unnamed_addr constant [9 x i8] c"Thursday\00", align 1
@.str.4 = private unnamed_addr constant [7 x i8] c"Friday\00", align 1
@.str.5 = private unnamed_addr constant [9 x i8] c"Saturday\00", align 1
@.str.6 = private unnamed_addr constant [7 x i8] c"Sunday\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  store i32 4, ptr %2, align 4
  %3 = load i32, ptr %2, align 4
  switch i32 %3, label %18 [
    i32 1, label %4
    i32 2, label %6
    i32 3, label %8
    i32 4, label %10
    i32 5, label %12
    i32 6, label %14
    i32 7, label %16
  ]

4:                                                ; preds = %0
  %5 = call i32 (ptr, ...) @printf(ptr noundef @.str)
  br label %18

6:                                                ; preds = %0
  %7 = call i32 (ptr, ...) @printf(ptr noundef @.str.1)
  br label %18

8:                                                ; preds = %0
  %9 = call i32 (ptr, ...) @printf(ptr noundef @.str.2)
  br label %18

10:                                               ; preds = %0
  %11 = call i32 (ptr, ...) @printf(ptr noundef @.str.3)
  br label %18

12:                                               ; preds = %0
  %13 = call i32 (ptr, ...) @printf(ptr noundef @.str.4)
  br label %18

14:                                               ; preds = %0
  %15 = call i32 (ptr, ...) @printf(ptr noundef @.str.5)
  br label %18

16:                                               ; preds = %0
  %17 = call i32 (ptr, ...) @printf(ptr noundef @.str.6)
  br label %18

18:                                               ; preds = %0, %16, %14, %12, %10, %8, %6, %4
  ret i32 0
}

declare i32 @printf(ptr noundef, ...) #1

; int main(){
; double *A, *B; int *C;
; for (int i = 0; i < 10; ++i) {
;   A[i] = B[C[i]];
; }
; }


define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca ptr, align 8
  %3 = alloca ptr, align 8
  %4 = alloca ptr, align 8
  %5 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  store i32 0, ptr %5, align 4
  br label %6

6:                                                ; preds = %23, %0
  %7 = load i32, ptr %5, align 4
  %8 = icmp slt i32 %7, 10
  br i1 %8, label %9, label %26

9:                                                ; preds = %6
  %10 = load ptr, ptr %3, align 8
  %11 = load ptr, ptr %4, align 8
  %12 = load i32, ptr %5, align 4
  %13 = sext i32 %12 to i64
  %14 = getelementptr inbounds i32, ptr %11, i64 %13
  %15 = load i32, ptr %14, align 4
  %16 = sext i32 %15 to i64
  %17 = getelementptr inbounds double, ptr %10, i64 %16
  %18 = load double, ptr %17, align 8
  %19 = load ptr, ptr %2, align 8
  %20 = load i32, ptr %5, align 4
  %21 = sext i32 %20 to i64
  %22 = getelementptr inbounds double, ptr %19, i64 %21
  store double %18, ptr %22, align 8
  br label %23

23:                                               ; preds = %9
  %24 = load i32, ptr %5, align 4
  %25 = add nsw i32 %24, 1
  store i32 %25, ptr %5, align 4
  br label %6, !llvm.loop !6

26:                                               ; preds = %6
  %27 = load i32, ptr %1, align 4
  ret i32 %27
}


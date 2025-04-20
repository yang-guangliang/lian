; #include <stdio.h>
 
; extern int func(void);
; // the definition of func is written in assembly language
; __asm__(".globl func\n\t"
;         ".type func, @function\n\t"
;         "func:\n\t"
;         ".cfi_startproc\n\t"
;         "movl $7, %eax\n\t"
;         "ret\n\t"
;         ".cfi_endproc");
 
; int main(void)
; {
;     int n = func();
;     // gcc's extended inline assembly
;     __asm__ ("leal (%0,%0,4),%0"
;            : "=r" (n)
;            : "0" (n));
;     printf("7*5 = %d\n", n);
;     fflush(stdout); // flush is intentional
 
;     // standard inline assembly in C++
;     __asm__ ("movq $60, %rax\n\t" // the exit syscall number on Linux
;              "movq $2,  %rdi\n\t" /x/ this program returns 2
;              "syscall");
; }


module asm ".globl func"
module asm "\09.type func, @function"
module asm "\09func:"
module asm "\09.cfi_startproc"
module asm "\09movl $7, %eax"
module asm "\09ret"
module asm "\09.cfi_endproc"

@.str = private unnamed_addr constant [10 x i8] c"7*5 = %d\0A\00", align 1
@stdout = external global ptr, align 8

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = call i32 @func()
  store i32 %2, ptr %1, align 4
  %3 = load i32, ptr %1, align 4
  %4 = call i32 asm "leal ($0,$0,4),$0", "=r,0,~{dirflag},~{fpsr},~{flags}"(i32 %3) #2, !srcloc !6
  store i32 %4, ptr %1, align 4
  %5 = load i32, ptr %1, align 4
  %6 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %5)
  %7 = load ptr, ptr @stdout, align 8
  %8 = call i32 @fflush(ptr noundef %7)
  call void asm sideeffect "movq $$60, %rax\0A\09movq $$2,  %rdi\0A\09syscall", "~{dirflag},~{fpsr},~{flags}"() #3, !srcloc !7
  ret i32 0
}

declare i32 @func() #1

declare i32 @printf(ptr noundef, ...) #1

declare i32 @fflush(ptr noundef) #1

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nounwind memory(none) }
attributes #3 = { nounwind }


; #include <stdio.h>
; int main(void)
; {
;     int no = 100, val ;
;     asm ("movl %1, %%ebx;"
;          "movl %%ebx, %0;"
;          : "=r" ( val )        /* output */
;          : "r" ( no )         /* input */
;          : "%ebx"         /* clobbered register */
;         );
; }


; Function Attrs: mustprogress noinline norecurse nounwind optnone uwtable
define dso_local noundef i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  store i32 100, ptr %1, align 4
  %3 = load i32, ptr %1, align 4
  %4 = call i32 asm "movl $1, %ebx;movl %ebx, $0;", "=r,r,~{ebx},~{dirflag},~{fpsr},~{flags}"(i32 %3) #1, !srcloc !6
  store i32 %4, ptr %2, align 4
  ret i32 0
}

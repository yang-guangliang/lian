; #include <stdio.h>

; // Define the Node struct
; typedef struct {
;     int value;      
;     float weight;   
; } Node;

; // Declare an array of Node structs
; Node nodes[10];

; // Example usage for the Node array
; void example1() {
;     nodes[2].weight = 5.5; // Access the weight field of the 3rd Node
; }

; // Define the Inner and Outer structs
; struct Inner {
;     int a;
;     float b;
; };

; struct Outer {
;     struct Inner inner;
;     double c;
; };

; // Example usage for the nested struct
; void example2() {
;     struct Outer o;  // Declare an instance of the Outer struct
;     o.inner.b = 3.14f; // Access the b field in the inner struct
; }

; int main() {
;     example1();
;     example2();
;     return 0;
; }

%struct.Node = type { i32, float }
%struct.Outer = type { %struct.Inner, double }
%struct.Inner = type { i32, float }

@nodes = dso_local global [10 x %struct.Node] zeroinitializer, align 16

; Function Attrs: mustprogress noinline nounwind optnone uwtable
define dso_local void @_Z8example1v() #0 {
  store float 5.500000e+00, ptr getelementptr inbounds ([10 x %struct.Node], ptr @nodes, i64 0, i64 2, i32 1), align 4
  ret void
}

; Function Attrs: mustprogress noinline nounwind optnone uwtable
define dso_local void @_Z8example2v() #0 {
  %1 = alloca %struct.Outer, align 8
  %2 = getelementptr inbounds %struct.Outer, ptr %1, i32 0, i32 0
  %3 = getelementptr inbounds %struct.Inner, ptr %2, i32 0, i32 1
  store float 0x40091EB860000000, ptr %3, align 4
  ret void
}

; Function Attrs: mustprogress noinline norecurse nounwind optnone uwtable
define dso_local noundef i32 @main() #1 {
  %1 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  call void @_Z8example1v()
  call void @_Z8example2v()
  ret i32 0
}

; struct RT {
;   char A;
; };

;  int *foo(struct RT **s) { 
;   return &s[1][4].A;
; }

%struct.RT = type { i8 }

; Function Attrs: noinline nounwind optnone uwtable
define dso_local ptr @foo(ptr noundef %0) #0 {
  %2 = alloca ptr, align 8
  store ptr %0, ptr %2, align 8
  %3 = load ptr, ptr %2, align 8
  %4 = getelementptr inbounds ptr, ptr %3, i64 1
  %5 = load ptr, ptr %4, align 8
  %6 = getelementptr inbounds %struct.RT, ptr %5, i64 4
  %7 = getelementptr inbounds %struct.RT, ptr %6, i32 0, i32 0
  ret ptr %7
}


; struct RT {
;   char A;
; };

; int *foo() {
;     struct RT s[10][1][4];
;     s[1][2][3].A = '7';
;     return 0;
; }

%struct.RT = type { i8 }

; Function Attrs: noinline nounwind optnone uwtable
define dso_local ptr @foo() #0 {
  %1 = alloca [10 x [1 x [4 x %struct.RT]]], align 16
  %2 = getelementptr inbounds [10 x [1 x [4 x %struct.RT]]], ptr %1, i64 0, i64 1
  %3 = getelementptr inbounds [1 x [4 x %struct.RT]], ptr %2, i64 0, i64 2
  %4 = getelementptr inbounds [4 x %struct.RT], ptr %3, i64 0, i64 3
  %5 = getelementptr inbounds %struct.RT, ptr %4, i32 0, i32 0
  store i8 55, ptr %5, align 1
  ret ptr null
}

; #include <stdio.h>

; typedef struct {
;     int value;
;     float weight;
; } Node;

; int main() {
;     // Declare two struct variables
;     Node n1 = { .value = 10, .weight = 5.5 };
;     Node n2;

;     // Assign n1 to n2
;     n2 = n1;

;     printf("Node n2 value: %d, weight: %.2f\n", n2.value, n2.weight);
;     return 0;
; }


%struct.Node = type { i32, float }
; ===================
@__const.main.n1 = private unnamed_addr constant %struct.Node { i32 10, float 5.500000e+00 }, align 4
@.str = private unnamed_addr constant [33 x i8] c"Node n2 value: %d, weight: %.2f\0A\00", align 1

; Function Attrs: mustprogress noinline norecurse optnone uwtable
define dso_local noundef i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca %struct.Node, align 4
  %3 = alloca %struct.Node, align 4
  store i32 0, ptr %1, align 4
  call void @llvm.memcpy.p0.p0.i64(ptr align 4 %2, ptr align 4 @__const.main.n1, i64 8, i1 false)
  call void @llvm.memcpy.p0.p0.i64(ptr align 4 %3, ptr align 4 %2, i64 8, i1 false)

  ; https://llvm.org/docs/LangRef.html#i-invoke
%ptrs = getelementptr double, ptr %B, <8 x i32> %C
; load 8 elements from array B into A
%A = call <8 x double> @llvm.masked.gather.v8f64.v8p0f64(<8 x ptr> %ptrs,
     i32 8, <8 x i1> %mask, <8 x double> %passthru)

  %retval = invoke i32 @Test(i32 15) to label %Continue      
            unwind label %TestCleanup              ; i32:retv   al set
  %retval = invoke coldcc i32 %Testfnptr(i32 15) to label %Continue
            unwind label %TestCleanup              ; i32:retval set

     
  %4 = getelementptr inbounds %struct.Node, ptr %3, i32 0, i32 0
  %5 = load i32, ptr %4, align 4
  %6 = getelementptr inbounds %struct.Node, ptr %3, i32 0, i32 1
  %7 = load float, ptr %6, align 4
  %8 = fpext float %7 to double
  %9 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %5, double noundef %8)
  ret i32 0
}

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: readwrite)
declare void @llvm.memcpy.p0.p0.i64(ptr noalias nocapture writeonly, ptr noalias nocapture readonly, i64, i1 immarg) #1

declare i32 @printf(ptr noundef, ...) #2

; struct RT {
;   char A;
;   int B[10][20];
;   char C;
; };
; struct ST {
;   int X;
;   double Y;
;   struct RT Z;
; };

; int *foo(struct ST *s) {
;   return &s[1].Z.B[5][13];
; }

%struct.ST = type { i32, double, %struct.RT }
%struct.RT = type { i8, [10 x [20 x i32]], i8 }

; Function Attrs: mustprogress noinline nounwind optnone uwtable
define dso_local noundef ptr @_Z3fooP2ST(ptr noundef %0) #0 {
  %2 = alloca ptr, align 8
  store ptr %0, ptr %2, align 8
  %3 = load ptr, ptr %2, align 8
  %4 = getelementptr inbounds %struct.ST, ptr %3, i64 1
  %5 = getelementptr inbounds %struct.ST, ptr %4, i32 0, i32 2
  %6 = getelementptr inbounds %struct.RT, ptr %5, i32 0, i32 1
  %7 = getelementptr inbounds [10 x [20 x i32]], ptr %6, i64 0, i64 5
  %8 = getelementptr inbounds [20 x i32], ptr %7, i64 0, i64 13
  ret ptr %8
}

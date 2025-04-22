; struct Point {
;     double x;
;     double y;
;     double z;
; };

; Point add_points(Point a, Point b) {
;   Point p;
;   p.x = a.x + b.x;
;   p.y = a.y + b.y;
;   p.z = a.z + b.z;
;   return p;
; }

%struct.__crt_locale_pointers = type { %struct.__crt_locale_data*, %struct.__crt_multibyte_data* }

%struct.Point = type { double, double, double }

define void @add_points(%struct.Point* noalias sret %agg.result,
                        %struct.Point* byval align 8 %a,
                        %struct.Point* byval align 8 %b) #0 {
; there is no alloca here for Point p;
; p.x = a.x + b.x;
  %1 = getelementptr inbounds %struct.Point, %struct.Point* %a, i32 0, i32 0
  %2 = load double, double* %1, align 8
  %3 = getelementptr inbounds %struct.Point, %struct.Point* %b, i32 0, i32 0
  %4 = load double, double* %3, align 8
  %5 = fadd double %2, %4
  %6 = getelementptr inbounds %struct.Point, %struct.Point* %agg.result, i32 0, i32 0
  store double %5, double* %6, align 8
; p.y = a.y + b.y;
  %7 = getelementptr inbounds %struct.Point, %struct.Point* %a, i32 0, i32 1
  %8 = load double, double* %7, align 8
  %9 = getelementptr inbounds %struct.Point, %struct.Point* %b, i32 0, i32 1
  %10 = load double, double* %9, align 8
  %11 = fadd double %8, %10
  %12 = getelementptr inbounds %struct.Point, %struct.Point* %agg.result, i32 0, i32 1
  store double %11, double* %12, align 8
; p.z = a.z + b.z;
  %13 = getelementptr inbounds %struct.Point, %struct.Point* %a, i32 0, i32 2
  %14 = load double, double* %13, align 8
  %15 = getelementptr inbounds %struct.Point, %struct.Point* %b, i32 0, i32 2
  %16 = load double, double* %15, align 8
  %17 = fadd double %14, %16
  %18 = getelementptr inbounds %struct.Point, %struct.Point* %agg.result, i32 0, i32 2
  store double %17, double* %18, align 8
; there is no real returned value, because the previous stores directly wrote
; to the caller allocated value via %agg.result
  ret void
}


; int main() {
;   Point a = {1.0, 3.0, 4.0};
;   Point b = {2.0, 8.0, 5.0};
;   Point c = add_points(a, b);
;   return 0;
; }

define i32 @main() #1 {
; these are the a, b, c in the scope of main
  %a = alloca %struct.Point, align 8
  %b = alloca %struct.Point, align 8
  %c = alloca %struct.Point, align 8
; these are copies, which are passed as arguments
  %1 = alloca %struct.Point, align 8
  %2 = alloca %struct.Point, align 8
; copy the global initializer main::a to %a
  %3 = bitcast %struct.Point* %a to i8*
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* %3, i8* bitcast (%struct.Point* @main.a to i8*), i64 24, i32 8, i1 false)
; copy the global initializer main::b to %b
  %4 = bitcast %struct.Point* %b to i8*
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* %4, i8* bitcast (%struct.Point* @main.b to i8*), i64 24, i32 8, i1 false)
; clone a to %1
  %5 = bitcast %struct.Point* %1 to i8*
  %6 = bitcast %struct.Point* %a to i8*
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* %5, i8* %6, i64 24, i32 8, i1 false)
; clone b to %2
  %7 = bitcast %struct.Point* %2 to i8*
  %8 = bitcast %struct.Point* %b to i8*
 call void @llvm.memcpy.p0i8.p0i8.i64(i8* %7, i8* %8, i64 24, i32 8, i1 false)
; call add_points with the cloned values
  call void @add_points(%struct.Point* sret %c, %struct.Point* byval align 8 %1, %struct.Point* byval align 8 %2)
  ; [...]
}
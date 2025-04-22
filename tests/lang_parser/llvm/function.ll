$g = comdat any
$h = comdat any

define void @f() align 2 {
0:
	ret void
}

define void @g() align 2 comdat {
; <label>:0
	ret void
}

define void @h() comdat align 2 {
; <label>:0
	ret void
}


define linkonce_odr dso_local i32 @vsprintf(i8* noundef %0, i8* noundef %1, i8* noundef %2) #0 comdat {

}

define linkonce_odr dso_local i32 @_vsnprintf(i8* noundef %0, i64 noundef %1, i8* noundef %2, i8* noundef %3) #0 comdat {

}

define dso_local void @addEdge(i32 noundef %0, i32 noundef %1, i32 noundef %2) #0 {

}

define dso_local void @swap(%struct.NODE* noundef %0, %struct.NODE* noundef %1) #0 {

}

define dso_local void @push(i32 noundef %0, i32 noundef %1) #0 {

}

define dso_local i64 @get() #0 {
}

define dso_local i32 @main() #0 {
}

define linkonce_odr dso_local i32 @scanf(i8* noundef %0, ...) #0 comdat {

}

define linkonce_odr dso_local i32 @printf(i8* noundef %0, ...) #0 comdat {

}
define linkonce_odr dso_local i32 @_vsprintf_l(i8* noundef %0, i8* noundef %1, %struct.__crt_locale_pointers* noundef %2, i8* noundef %3) #0 comdat {
}

define linkonce_odr dso_local i32 @_vsnprintf_l(i8* noundef %0, i64 noundef %1, i8* noundef %2, %struct.__crt_locale_pointers* noundef %3, i8* noundef %4) #0 comdat {
}

define linkonce_odr dso_local i64* @__local_stdio_printf_options() #0 comdat {

}

define linkonce_odr dso_local i64* @__local_stdio_scanf_options() #0 comdat {

}

define linkonce_odr dso_local i32 @_vfprintf_l(%struct._iobuf* noundef %0, i8* noundef %1, %struct.__crt_locale_pointers* noundef %2, i8* noundef %3) #0 comdat {

define void @f(%struct.T* byval(%struct.T) align 4 %0) {

}

define void @g(%struct.T* byval align 4 %0) {

}

define void @f(i8* %target) {
}

define private i32 @Foo() nounwind {
    ret i32 17
}


define i32 @main(i32 %argc, i8** %argv) nounwind {
    ; printf("Argument count: %d\n", argc)
    %1 = call i32 (i8*, ...) @printf(i8* getelementptr([20 x i8], [20 x i8]* @.textstr, i32 0, i32 0), i32 %argc)
    ret i32 0
}


define i32 @_Z8functionii(i32 %a, i32 %b) #0 {
; [...]
  ret i32 %5
}

define double @_Z8functionddd(double %a, double %b, double %x) #0 {
; [...]
  ret double %8
}

define void @add_points(%struct.Point* noalias sret %agg.result,
                        %struct.Point* byval align 8 %a,
                        %struct.Point* byval align 8 %b) #0 {

} 
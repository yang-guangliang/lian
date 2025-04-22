function a() {
    console.log(a);
}
function internal() {
    i = 0;
    a();
    if (i == 0) {
        a = 4;
    }
    // a();
}
internal();


import deviceInfo from "@ohos:deviceInfo";
// harlibrary's src/main/ets/utils/Calc.ets
export class Calc1 {
    public static staticAdd(a: number, b: number): number {
        let c = a + b;
        console.info('DynamicImport I am harlibrary in staticAdd, %d + %d = %d', a, b, c);
        return c;
    }
    public instanceAdd(a: number, b: number): number {
        let c = a + b;
        console.info('DynamicImport I am harlibrary in instanceAdd, %d + %d = %d', a, b, c);
        return c;
    }
}
export function addHarlibrary(a: number, b: number): number {
    let c = a + b;
    console.info('DynamicImport I am harlibrary in addHarlibrary, %d + %d = %d', a, b, c);
    console.info(deviceInfo.brand);
    return c;
}

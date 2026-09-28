import hilog from "@ohos:hilog";
export function func1(ap: apple): void {
    ap.change_price(5);
    hilog.info(0x0000, 'testTag', ap.msg);
}
export class apple {
    price: number = 6;
    msg: string = "notaint";
    change_price(p: number): void {
        this.price = p;
    }
}
export let tmp = 8;

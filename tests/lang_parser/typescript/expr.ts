import { IProps,Component,IRenderable } from './IProps';
import  * as React from 'react';
import {a as b, c as d} from './IProps';

var sum = (x: number, y: number) => x + y;

try {
    console.log(sum(3, 4));
}
catch (e) {
    console.log(e);
}
finally {
    console.log("Finally block");
}

throw new Error("This is an error");

var m;

m = input("Enter a number");

if (m > 5)
    {
        console.log("Number is greater than 5");
    }
else
    {
        console.log("Number is less than or equal to 5");
    }


export interface ButtonProps extends IProps {
    label: string;
    onClick: () => void;
}

class Component<T extends IProps> {
    a = 3;
    props: T;
    constructor(props: T) {
        this.props = props;
    }
}


function input(message: string): number {
    return parseInt(prompt(message));
}


class Button extends Component<ButtonProps> implements IRenderable<ButtonProps> {
    render(): void {
        console.log("Rendering button");
        this.props.onClick();
    }
}

var day;

switch (day) {
    case 0:
        console.log("It is a Sunday.");
        break;
    case 1:
        console.log("It is a Monday.");
        break;
    case 2:
        console.log("It is a Tuesday.");
        break;
    case 3:
        console.log("It is a Wednesday.");
        break;
    case 4:
        console.log("It is a Thursday.");
        break;
    case 5:
        console.log("It is a Friday.");
        break;
    case 6:
        console.log("It is a Saturday.");
        break;
    default:
        console.log("No such day exists!");
        break;
}

for (let i = 0; i < 10; i++) {
    console.log(i);
}

let i = 0;

do {
    console.log("Hello");
}while (i++ < 10);

while (i++ < 30) {
    console.log("Hello");
}

function transformArray<T, U>(
    items: T[], 
    transform: (item: T) => U, 
    separator: string = ','
  ): string {
    return items.map(item => transform(item)).join(separator);
}
// variable and lexical declaration
var p, q = 1, r = 2 + 3;

let [x, y] = [1, 2];

let {name, age} = person;

let {name: n, age: a} = person;

const obj2 = {
  *g() {
    let index = 0;
    while (true) {
      yield index++;
    }
  },
};


// function declaration
// case 1
export default function multiply(multiplier, ...theArgs) {
  return theArgs.map((element) => multiplier * element);
};

// case 2
function callSomething(thing = something()) {
  return thing;
}

// case 3
async function* foo() {
  yield await Promise.resolve('a');
  yield await Promise.resolve('b');
}


// class declaration
// case 1
export class ColorWithAlpha extends Color {
  alpha;
  constructor(r, g, b, a) {
    super(r, g, b);
    this.alpha = a;
  }
  get alpha() {
    return this.alpha;
  }
  set alpha(value) {
    if (value < 0 || value > 1) {
      throw new RangeError("Alpha value must be between 0 and 1");
    }
    this.alpha = value;
  }
  m = 6;
  static n = 7;
}

// case 2
const A = class {
  static field = 1 + 2 + 3;
  static {
    console.log(this.field);
  }
}

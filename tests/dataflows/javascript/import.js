import { func1, func2 } from "../utility";

const Handler= {
  func1,
  func2
};

Handler["func1"]("sic mundus");
Handler["func2"]("creatus est");

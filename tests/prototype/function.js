function hh(name) {
    this.name = name;
}

hh.prototype.sayhello = function bb(n) {
    this.name = n;
};

aa = hh.prototype;
// ee = aa
// dd = hh.sayhello
const cc = new hh();
p = cc.__proto__;

q = cc.sayhello;


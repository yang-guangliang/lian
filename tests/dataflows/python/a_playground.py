# def func1():
#     a = source()
#     c = a.b.h
#     m = prop(c)
#     sink(a)
# func1()
latents_ubyte = (
    a.mul(0xFF)  # change scale from -1..1 to 0..1  # to 0..255
).to(device="cpu", dtype=torch.uint8)
a = pickle.loads(latents_ubyte)

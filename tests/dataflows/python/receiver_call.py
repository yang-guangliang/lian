def func():
    f = 3
    g = 4

a = 3
a.b = func
a = a.b(self.config.generator.pad_token_id)
v = a.b

pad_mask = a.eq(self.config.generator.pad_token_id)

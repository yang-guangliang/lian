class Container:
    def __init__(self):
        self.inner = None
        self.val = 0

def objects_flow(obj1, obj2):
    # Direct field writes and chained reads
    obj1.inner = obj2
    obj2.val = 10
    
    # Nested field access
    extracted = obj1.inner.val
    
    # Dynamic field assignment (Python specific object manipulation)
    obj1.dynamic_field = "dynamic_test_value"
    
    return extracted, obj1.dynamic_field

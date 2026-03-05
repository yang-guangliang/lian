class Node:
    def __init__(self, value):
        self.value = value
        self.visited = False
        
    def get_value(self):
        return self.value

def classes_flow():
    # Instantiation 
    node1 = Node(1)
    
    # Method invocation 
    val = node1.get_value()
    
    return val

class TaintAnalysis:
    def __init__(self, lian, options, loader):
        self.options = options
        self.lian = lian
        self.loader = loader

    def analyze(self, entry_point, call_tree, sfg):
        pass

    def run(self, entry_point):
        for entry_point in self.loader.get_entry_points():
            call_tree = self.loader.get_call_tree(entry_point)
            sfg = self.loader.get_sfg(entry_point)
            self.analyze(entry_point, call_tree, sfg)
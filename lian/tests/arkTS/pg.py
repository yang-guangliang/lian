
# permissions = ['location', 'camera']
# def reqpermission(permissions):
#     grant(permissions)
class entryablility:
    def onwindowstagecreated(self):
        print("window stage created")
    def onwindowstagechanged(self):
        print("window stage changed")

ea = entryablility()

ea.onwindowstagecreated()
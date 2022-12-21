class Fart:
    def __init__(self):
        self.s = "Stinky"


class Test(Fart):
    def __init__(self):
        super(Test, self).__init__()
        self.start()

    def start(self):
        self.s = "Fart"


s = Fart()
print(s.s)
test = Test(s)
print(s.s)
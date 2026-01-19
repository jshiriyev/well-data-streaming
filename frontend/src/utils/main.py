class STATE():

    def __init__(self,curves=None):

        self.curves = (curves or [])

    @property
    def trails(self):
        return len(self.curves)
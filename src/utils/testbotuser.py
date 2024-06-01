class TestBotUser:
    test_bot_id = -1

    def __init__(self):
        self.name = "Test Bot"
        self.id = self.test_bot_id

    def __str__(self):
        return self.name

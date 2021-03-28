from unittest.mock import MagicMock


class MockDiscordBase(MagicMock):

    def __init__(self, default_values: dict, **kwargs):
        super().__init__()

        # ensure no bad keys passed
        for k in kwargs.keys():
            assert k in default_values

        # set default attributes / overrides
        for k, v in default_values.items():
            if k in kwargs:
                self.__setattr__(k, kwargs[k])
            else:
                self.__setattr__(k, v)

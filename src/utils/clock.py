import asyncio


class Clock:
    """Mini Blocking Clock class for some sense of timing in the game. Calls
    `condition` at every `rate` seconds, with remaining time in `int` as
    only argument.

    All time values are in seconds.
        - `condition` must be a coroutine
        - if `condition` returns `false`, the clock stops counting down
          and yield control back to the calling task

    Start clock with
    ```py
    await clock.start()
    ```

    If clock expires early, returns the result of `condition`.

    :param duration: Time to integrate clock over
    :param condition: Callback function to early exit clock
    :type condition: function, optional
    :param rate: How often to call `condition` (seconds, default=1).
    :param default_return: What the clock should return as the default value
    on expiry (default {})
    :type default_return: function, optional
    """

    def __init__(self, duration: int, condition=None, rate=1, default_return=None):
        self.duration = duration
        self.condition = condition
        self.integrator = 0
        self.rate = rate
        self.default_return = {} if default_return is None else default_return

    async def start(self):
        """Start the clock integration. Calls `self.condition` every `self.rate` seconds.
        If `self.condition` returns non-falsey result, will exit and return the result. Else
        keeps integrating, and returns `self.default_return` one clock is expired.

        :return: Result of `self.condition`, or `self.default_return`.
        """
        while self.integrator < self.duration:
            self.integrator += 1

            await asyncio.sleep(self.rate)
            if self.condition is not None:
                result = await self.condition(self.duration - self.integrator)
                if result:
                    return result

        return self.default_return

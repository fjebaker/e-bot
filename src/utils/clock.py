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
    """

    def __init__(self, duration, condition=None, rate=1):
        self.duration = duration
        self.condition = condition
        self.integrator = 0
        self.rate = rate

    async def start(self):
        while self.integrator < self.duration:
            self.integrator += 1

            await asyncio.sleep(self.rate)
            if self.condition is not None:
                result = await self.condition(self.duration - self.integrator)
                if result:
                    return result

        return None

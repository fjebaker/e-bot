from unittest.mock import patch, call, AsyncMock

import pytest

from utils.clock import Clock


@pytest.fixture(scope="module", autouse=True)
def disablesleep(no_sleep):
    ...


def test_constructor():
    # ensure interface values stored
    c = Clock(5)

    assert c.duration == 5
    assert c.condition == None
    assert c.integrator == 0
    assert c.default_return == {}

    # ensure default_return is stored
    c = Clock(5, default_return={"test": "value"})
    assert c.default_return == {"test": "value"}

    # test negative
    with pytest.raises(AssertionError):
        Clock(-5)

    # test 0
    with pytest.raises(AssertionError):
        Clock(0)

    # test rate parameter
    with pytest.raises(AssertionError):
        Clock(1, rate=5)

    c = Clock(5, rate=2)
    assert c.rate == 2


@pytest.mark.asyncio
async def test_simple_start():
    # ensure integrator count and exits work
    c = Clock(100)
    ret = await c.start()
    assert ret == c.default_return
    assert c.integrator == 100


@pytest.mark.asyncio
async def test_callbacks():
    # ensure callbacks work
    cb = AsyncMock()
    cb.return_value = False

    c = Clock(5, condition=cb)
    ret = await c.start()

    assert ret == c.default_return
    cb.assert_has_calls([call(4 - i) for i in range(5)])


@pytest.mark.asyncio
async def test_early_exit():
    # ensure early exit works
    cb = AsyncMock()
    _test_resp = {"test": "some-ret-value"}
    cb.return_value = _test_resp

    c = Clock(5, condition=cb)
    ret = await c.start()
    assert ret == _test_resp
    assert c.integrator == 1


@pytest.mark.asyncio
async def test_rate(no_sleep):
    # reset call count
    no_sleep.call_count = 0

    # ensure sleep duration is rate
    c = Clock(100, rate=10)
    ret = await c.start()

    no_sleep.assert_called_with(10)
    assert no_sleep.call_count == 10

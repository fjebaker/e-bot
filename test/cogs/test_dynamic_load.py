import pytest

from unittest.mock import call

from cogs.dynamic_load import DynamicLoad

# fixtures


@pytest.fixture
def dynamic_load(bot):
    mock_load = DynamicLoad(bot)

    mock_load.bot.extensions = {"cogs.dynamic_load": None, "cogs.test_cog": None}

    return mock_load


@pytest.fixture(autouse=True)
def reset_dynamic_load(dynamic_load):
    for i in dynamic_load.bot.__dict__["_mock_children"].values():
        i.side_effect = None


# tests


def test_reload_cog(dynamic_load):
    assert dynamic_load._reload_cog("cogs.test_cog") == "Reloaded `cogs.test_cog`"
    dynamic_load.bot.reload_extension.assert_has_calls([call("cogs.test_cog")])

    assert dynamic_load._reload_cog("cogs.new_cog") == "Loaded new cog `cogs.new_cog`"
    dynamic_load.bot.load_extension.assert_has_calls([call("cogs.new_cog")])

    dynamic_load.bot.load_extension.side_effect = Exception("test_exception")
    assert dynamic_load._reload_cog("cogs.new_cog") == "No such cog: `cogs.new_cog`"

    dynamic_load.bot.reload_extension.side_effect = Exception("test_exception")
    assert (
        dynamic_load._reload_cog("cogs.test_cog")
        == "`cogs.test_cog` raised exception: ```\ntest_exception\n```"
    )


def test_reload_all_cogs(dynamic_load):
    assert dynamic_load._reload_all_cogs() == ["cogs.test_cog"]
    dynamic_load.bot.reload_extension.assert_has_calls([call("cogs.test_cog")])


def test_fmt_cog_list(dynamic_load):
    ret = dynamic_load._fmt_cog_list(["cogs.new_cog", "cogs.test_cog"])
    assert ret == "```\n- cogs.new_cog\n- cogs.test_cog\n```"

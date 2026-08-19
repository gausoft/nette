from nette.engine import check_files
from nette.rules.shape import ArgumentCount

ENDPOINT = (
    "@app.get('/users')\n"
    "async def list_users(a, b, c, d, e, f, g, h):\n"
    "    return a\n"
)

ROUTER_ENDPOINT = (
    "@router.post('/orders')\n"
    "def create_order(a, b, c, d, e, f, g, h):\n"
    "    return a\n"
)

PLAIN_FUNCTION = "def helper(a, b, c, d, e, f, g, h):\n    return a\n"


def check(file, framework=None):
    return check_files([file], rules=[ArgumentCount()], framework=framework)


def test_endpoint_exempt_under_fastapi_profile(write_file):
    file = write_file(ENDPOINT)

    assert check(file, framework="fastapi") == []


def test_router_decorator_also_exempt(write_file):
    file = write_file(ROUTER_ENDPOINT)

    assert check(file, framework="fastapi") == []


def test_plain_function_still_flagged_under_fastapi_profile(write_file):
    file = write_file(PLAIN_FUNCTION)

    assert [f.code for f in check(file, framework="fastapi")] == ["NET103"]


def test_endpoint_flagged_without_profile(write_file):
    file = write_file(ENDPOINT)

    assert [f.code for f in check(file)] == ["NET103"]

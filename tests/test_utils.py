import context  # noqa


def test_get_own_ip():
    ip = context.get_own_ip()
    assert ip is not None

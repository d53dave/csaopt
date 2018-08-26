import pytest

from context import Runner, ExecutionType, get_configs

try:
    import docker

    class MockContext():
        def __init__(self):
            self.obj = {}

    def test_runner_langermann():
        internal_conf = get_configs('csaopt/internal/csaopt-internal.conf')
        ctx = {}
        ctx['internal_conf'] = internal_conf

        runner = Runner(['examples/langermann/langermann_opt.py'],
                        ['examples/langermann/langermann_opt.conf'], ctx)

        runner.run()
        if len(runner.failures) > 0:
            raise Exception('Runner had failures: %s' % runner.failures)


except Exception:
    pass

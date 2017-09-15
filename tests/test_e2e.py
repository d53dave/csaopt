import pytest
import os
import subprocess

from pathlib import Path


@pytest.mark.skipif(not os.getenv('CSAOPT_RUN_E2E'),
                    reason='E2E Tests are disabled by default. Set the CSAOPT_RUN_E2E env variable to enable')
def test_end2end():
    conf_path = Path('tests/e2e/csaopt_e2e.conf').resolve()
    model_path = Path('test/e2e/model/').resolve()

    try:
        csaopt_proc = subprocess.Popen(
                                ['csaopt', '-conf', conf_path.name, '--model', model_path.name],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        out, err = csaopt_proc.communicate()
        returncode = csaopt_proc.returncode

        assert returncode == 1
        assert len(err) is 0
        assert '(0, 0)' in out

    finally:
        subprocess.Popen(['csaopt', '--cleanup'])
        returncode = csaopt_proc.returncode

        if returncode is not 0:
            assert not """
            **WARNING** csaopt --cleanup exited with a non-zero result
            ==========================================================

            This usually means that it could not successfully terminate
            all instances that it provisioned on the cloud service.

            ** MAKE SURE TO MANUALLY CHECK AND TERMINATE INSTANCES   **
            ** IN THE CSAOPT GROUP/TAG. RUNNING MACHINES CONTINUE TO **
            ** INCUR COSTS. YOU HAVE BEEN WARNED!                    **
            """

import os
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor

# Basic example taken from https://stackoverflow.com/a/35507743/2822762

_Options = namedtuple(
                'Options',
                ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection',
                 'module_path', 'forks', 'remote_user', 'private_key_file',
                 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                 'scp_extra_args', 'become', 'become_method', 'become_user',
                 'verbosity', 'check'])


class AnsibleManager():
    def __init__(self, internal_conf):
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.inventory = Inventory(
                            loader=self.loader,
                            variable_manager=self.variable_manager,
                            host_list='/home/slotlocker/hosts2')

        playbook_path = internal_conf['ansible.playbook_path']

        if not os.path.isfile(playbook_path):
            raise AssertionError('Could not load ansible playbook')

        self.options = _Options(
                            listtags=False, listtasks=False, listhosts=False,
                            syntax=False, connection='ssh', module_path=None,
                            forks=100, remote_user='slotlocker', private_key_file=None,
                            ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None,
                            scp_extra_args=None, become=True, become_method=None,
                            become_user='root', verbosity=None, check=False)

        self.variable_manager.extra_vars = {'hosts': 'mywebserver'}  # This can accomodate various other command line arguments.`
        passwords = {}

        self.playbook_executor = PlaybookExecutor(
                                playbooks=[playbook_path],
                                inventory=self.inventory,
                                variable_manager=self.variable_manager,
                                loader=self.loader,
                                options=self.options,
                                passwords=passwords)

        def setup_instances():
            self.playbook_executor.run()
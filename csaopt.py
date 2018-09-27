#!/usr/bin/env python3

import sys
import click
from csaopt.utils import internet_connectivity_available, get_configs
from csaopt import Runner
from csaopt import __appname__ as csaopt_name
from csaopt import __version__ as csaopt_version

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@click.group()
@click.version_option(version=csaopt_version, prog_name=csaopt_name)
@click.pass_context
def cli(ctx):
    try:
        internal_conf = get_configs('csaopt/internal/csaopt-internal.conf')
        ctx.obj['internal_conf'] = internal_conf
    except Exception as e:
        eprint('Could not load configs', e)
        sys.exit(1)


@cli.command(name='run', help='Run the optimization based on the provided config and model.')
@click.option(
    '--model',
    type=click.Path(exists=True, resolve_path=True),
    help='Folder containing the model that should be used for optimization.')
@click.option(
    '--conf',
    type=click.Path(exists=True, resolve_path=True),
    help='Path to the CSAOpt config. If not provided, \'conf/csaopt.conf\' will be used')
@click.pass_context
def run_opt(ctx, model, conf):
    runner = Runner([model], [conf], ctx.obj)
    runner.run()
    runner.console_printer.print_magenta('Bye.\n')


@cli.command(name='check', help='Check and validate the provided configuration and model.')
@click.option(
    '--model',
    type=click.Path(exists=True, resolve_path=True),
    help='Folder containing the model that should be used for optimization.')
@click.option(
    '--conf',
    default='conf/csaopt.conf',
    type=click.Path(exists=True, resolve_path=True),
    help='Path to the CSAOpt config. If not provided, \'conf/csaopt.conf\' will be used')
@click.option(
    '--with-aws',
    is_flag=True,
    default=False,
    help='If enabled, the check will also spin up EC2 instances to verify configuration and communication.')
def run_check(**kwargs):
    print('Check called')


@cli.command(name='cleanup', help='Clean up generated files and terminate any running EC2 instances')
def cleanup():
    pass


if __name__ == '__main__':
    cli(obj={})

"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from lib import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=csaopt', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name = 'CSAOpt',
    version = __version__,
    description = 'Cloud based simulated annealing optimization framework',
    long_description = long_description,
    url = 'https://github.com/d53dave/csaopt',
    author = 'David Sere',
    author_email = 'dave@d53dev.net',
    license = 'UNLICENSE',
    classifiers = [
        'Intended Audience :: Developers, Scientists',
        'Topic :: Scientific',
        'License :: MIT',
        'Natural Language :: English',
        'Operating System :: GNU/Linux',
        'Programming Language :: Python :: 3.6',
    ],
    keywords = 'cli',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires = ['docopt'],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    entry_points = {
        'console_scripts': [
            'csaopt=csaopt.cli:main',
        ],
    },
    cmdclass = {'test': RunTests},
)

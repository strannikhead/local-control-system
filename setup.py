from setuptools import setup
import os
import platform


def add_to_path_if_not_exists(directory):
    paths = os.environ['PATH'].split(os.pathsep)
    if directory not in paths:
        os.environ['PATH'] += os.pathsep + directory


def add_to_profile_if_not_exists(directory):
    system = platform.system()
    if system == 'Linux' or system == 'Darwin':
        profile_path = os.path.expanduser('~/.bashrc')
        if not os.path.exists(profile_path):
            profile_path = os.path.expanduser('~/.bash_profile')
        if os.path.exists(profile_path):
            with open(profile_path, 'a') as profile:
                profile.write('\nexport PATH="{}:$PATH"\n'.format(directory))
    elif system == 'Windows':
        os.environ['PATH'] += os.pathsep + directory


app_installation_path = ''

add_to_path_if_not_exists(app_installation_path)
add_to_profile_if_not_exists(app_installation_path)

setup(
    name='cvs',
    version='1.0',
    py_modules=['cvs', 'utils', 'exceptions', 'gui'],
    entry_points={
        'console_scripts': [
            'cvs=cvs:cli'
        ],
    },
)

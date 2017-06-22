"""The configuration file can be one of these places and are checked in the
order mentioned below, if it is found, the search terminates:

- $PWD/paper-git.cfg
- $HOME/paper-git.cfg
- /etc/paper-git.cfg
 """

import os
import sys

from flufl.lock import Lock
from lazr.config import ConfigSchema
from paper_to_git.utilities import makedirs
from pkg_resources import resource_filename
from string import Template

from paper_to_git.database import BaseDatabase

__all__ = [
    'BaseConfig',
    'TestingConfig',
    ]

SPACERS = '\n'

CFG_TEMPLATE = """\
# AUTOMATICALLY GENERATED BY PAPER-TO-GIT
#
# This is a basic configuration template for the user configuration of
# Paper-to-Git. You can edit this file to configure Paper-To-Git with
# your variables and it will never be overwritten."""


class BaseConfig:
    DEBUG = False
    TESTING = False

    def __init__(self):
        self._config = None
        self.create_paths = True
        self.filename = None
        self.initialized = False
        self.dbox = None
        self.db = BaseDatabase(None)

    def __getattr__(self, name):
        return getattr(self._config, name)

    def __iter__(self):
        return iter(self._config)

    def load(self, filename=None):
        """Load the configuration from config files.
        """
        schema_file = resource_filename('paper_to_git.config', 'schema.cfg')
        schema = ConfigSchema(schema_file)
        config_file = resource_filename('paper_to_git.config', 'paper-git.cfg')
        self._config = schema.load(config_file)
        if filename is None:
            self._post_process()
        else:
            self.filename = filename
            with open(filename, 'r', encoding='utf-8') as user_config:
                self.push(filename, user_config.read())
        self.initialized = True

    def push(self, config_name, config_string):
        self._config.push(config_name, config_string)
        self._post_process()

    def pop(self, config_name):
        self._config.pop(config_name)
        self._post_process()

    def _post_process(self):
        # Expand all configuration related paths and ensure that the
        # directories exists.
        self._expand_paths()
        self.ensure_directories_exist()

    def _expand_paths(self):
        """Expand all the configuration paths"""
        layout = 'paths.' + self._config.main.layout
        for category in self._config.getByCategory('paths'):
            if category.name == layout:
                break
        else:
            print("No path configuration found: ", layout, file=sys.stderr)
            sys.exit(1)
        var_dir = category.var_dir
        substitutions = dict(
            cwd=os.getcwd(),
            var_dir=var_dir,
        )
        # Directories.
        for name in ('log', 'data', 'etc', 'cache'):
            key = '{}_dir'.format(name)
            substitutions[key] = getattr(category, key)
        # Files.
        for name in ('lock', 'pid'):
            key = '{}_file'.format(name)
            substitutions[key] = getattr(category, key)
        # Add the user provided configuration file.
        if self.filename is not None:
            substitutions['cfg_file'] = self.filename
        # Now perform substitutions recursively until there are no more
        # variables with $-vars in them.
        last_dollar_count = 0
        while True:
            expandables = []
            for key in substitutions:
                raw_value = substitutions[key]
                value = Template(raw_value).safe_substitute(substitutions)
                if '$' in value:
                    expandables.append((key, value))
                substitutions[key] = value
            if len(expandables) == 0:
                break
            if len(expandables) == last_dollar_count:
                print('Path expansion loop detected: \n',
                      SPACERS.join('\t{}: {}'.format(key, value)
                                   for key, value in sorted(expandables)),
                      file=sys.stderr)
                sys.exit(1)
            last_dollar_count = len(expandables)
        # Ensure that all the paths are made absolute.
        for key, value in substitutions.items():
            attribute = key.upper()
            setattr(self, attribute, os.path.abspath(value))

    @property
    def paths(self):
        """Return a dictionary of all the path variables"""
        return dict((k, self.__dict__[k])
                    for k in self.__dict__
                    if k.endswith('_DIR'))

    def ensure_directories_exist(self):
        """Create all the paths if the directories do not exist."""
        if self.create_paths:
            for path_name, path in self.paths.items():
                makedirs(path)
            # Create a paper-git.cfg file if it already doesn't exist.
            lock_file = os.path.join(self.VAR_DIR, 'paper-git-cfg.lck')
            paper-git_cfg = os.path.join(self.ETC_DIR, 'paper-git.cfg')
            with Lock(lock_file):
                if not os.path.exists(paper-git_cfg):
                    with open(paper-git_cfg, 'w') as fp:
                        print(CFG_TEMPLATE, file=fp)


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True

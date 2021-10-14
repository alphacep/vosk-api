import os
import glob
import logging
import shutil
import sys

ENV_VAR = 'GENTLE_RESOURCES_ROOT'

class SourceResolver:
    def __init__(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, os.pardir))

    def get_binary(self, name):
        path_in_project = os.path.join(self.project_root, name)
        if os.path.exists(path_in_project):
            return path_in_project
        else:
            return name

    def get_resource(self, name):
        root = os.environ.get(ENV_VAR) or self.project_root
        return os.path.join(root, name)

    def get_datadir(self, name):
        return self.get_resource(name)

class PyinstallResolver:
    def __init__(self):
        self.root = os.path.abspath(os.path.join(getattr(sys, '_MEIPASS', ''), os.pardir, 'Resources'))

    def get_binary(self, name):
        return os.path.join(self.root, name)

    def get_resource(self, name):
        rpath = os.path.join(self.root, name)
        if os.path.exists(rpath):
            return rpath
        else:
            return get_datadir(name) # DMG may be read-only; fall-back to datadir (ie. so language models can be added)

    def get_datadir(self, path):
        return os.path.join(os.environ['HOME'], '.gentle', path)

RESOLVER = PyinstallResolver() if hasattr(sys, "frozen") else SourceResolver()


def get_binary(name):
    return RESOLVER.get_binary(name)

def get_resource(path):
    return RESOLVER.get_resource(path)

def get_datadir(path):
    return RESOLVER.get_datadir(path)

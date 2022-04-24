# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import json
import os

CONFIG_FILE_PATH = "./settings/config.json"


def init_configuration():
    if not os.path.exists(CONFIG_FILE_PATH):
        raise Exception(f"File not found: {CONFIG_FILE_PATH}")

    conf_file = open(CONFIG_FILE_PATH, "r+")
    configuration = json.loads(conf_file.read())
    return configuration


class ConfigurationService:
    def __init__(self):
        self._configuration = init_configuration()

    def get_configuration(self, key=None):
        if key in self._configuration:
            return self._configuration[key]
        return None

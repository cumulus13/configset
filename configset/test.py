from __future__ import print_function
import os
from configset import configset
configname = os.path.join(os.path.dirname(__file__), 'test.ini')
configname2 = os.path.join(os.path.dirname(__file__), 'test2.ini')
print("test configname =", configname)
cfg = configset(configname)
#cfg.configname = configname2
cfg.get_config("GENERAL", "data")
data = cfg.sections()
print("data =", data)

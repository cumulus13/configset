from __future__ import print_function
import os
from configset import configset
cfg = configset()
data = cfg.get_config("DATABASE", 'host', '127.0.0.1')
print("data =", data)


# configset

simple write config/setting, wrap of configparser


## Installing


Install and update using `pip`:

```bash:
$ pip install configset
```

configset supports Python 2 and newer, Python 3 and newer, and PyPy.

## Example

What does it look like? Here is an example of a simple configset program:

```python:

import configset
from pathlib import Path #for last version of python 2.7 and 3.+

class pcloud(object):

    def __init__(self, **kwargs):
        ...
        #self.CONFIG = configset(os.path.join(os.path.dirname(__file__), 'config.ini')) #for python start from 2.5 
        self.CONFIG = configset(str(Path(__file__).parent / 'config.ini') #for python or just
        #self.CONFIG = configset() #this will create *.ini file base on this file name
        ...

        self.username = self.CONFIG.get_config('AUTH', 'username', "admin") # 'admin' is default value
        self.password = self.CONFIG.get_config('AUTH', 'password', "12345678") # "12345678" is default value

        self.port = self.CONFIG.get_config_as_list('MAIN', 'PORTS') # outputs is list, example ['8181', '55', '32']
        self.host = self.CONFIG.write_config('MAIN', 'HOST', '127.0.0.1')  # this will write HOST = '127.0.0.1' on section [MAIN]
        ...
```

## Support

*   Python 2.7+, 3.x+
*   Windows, Linux

## author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 [Support me on Patreon](https://www.patreon.com/cumulus13)
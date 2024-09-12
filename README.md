
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

class pcloud(object):

    def __init__(self, **kwargs):
        ...
        self.CONFIG.configname = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.CONFIG = configset.configset(self.CONFIG.configname)
        ...

        self.username = self.CONFIG.read_config('AUTH', 'username', "admin")
        self.password = self.CONFIG.read_config('AUTH', 'password', "12345678")
        ...
```

## Support

*   Python 2.7 +, 3.x+
*   Windows, Linux

## author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 [Support me on Patreon](https://www.patreon.com/cumulus13)

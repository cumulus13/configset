@echo off
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q configset.egg-info
rmdir /s /q __pycache__
setup.py sdist bdist_wheel
twine upload dist\* -r pypihub
twine upload dist\*

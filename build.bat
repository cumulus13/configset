@echo off
if "%1"=="build" goto build
if "%1"=="1" goto build
if "%1"=="upload" goto upload
if "%1"=="pypihub" goto pypihub

rmdir /s /q build
rmdir /s /q dist
rmdir /s /q configset.egg-info
rmdir /s /q __pycache__
setup.py sdist bdist_wheel
twine upload dist\* -r pypihub
twine upload dist\*
goto end

:build
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q configset.egg-info
rmdir /s /q __pycache__
setup.py sdist bdist_wheel
twine upload dist\* -r pypihub
goto end

:upload
twine upload dist\* -r pypihub
twine upload dist\*
goto end

:pypihub
twine upload dist\* -r pypihub
goto end

:pypi
twine upload dist\*
goto end


:end

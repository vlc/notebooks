rem call using:
rem setup_emme_venv

echo off
rem Replace username and password below
: set HTTP_PROXY=http://username:password@www-proxy.qdot.qld.gov.au:8080
: set HTTPS_PROXY=https://username:password@www-proxy.qdot.qld.gov.au:8080
echo on

pip install virtualenv
virtualenv --python="%EMMEPATH%"\python27\python.exe .venv_emme
copy "%EMMEPATH%"\emme.pth .venv_emme\Lib\site-packages\

rem activate the emme Virtual Env
call .venv_emme\Scripts\activate.bat

rem Upgrade pip to latest
python -m pip install --upgrade pip

rem The version of the zip file commited to the project was created by taking the version
rem from here: http://www.gaia-gis.it/gaia-sins/windows-bin-amd64/mod_spatialite-4.3.0a-win-amd64.7z
rem and updating the libstdc++_64-6.dll and libgcc_s_seh-1.dll files with newer versions from msys
rem as described in this guide: https://github.com/sqlitebrowser/sqlitebrowser/wiki/SpatiaLite-on-Windows
python bin/unzip_mod_spatialite.py

rem TODO: If we want to provide GDAL or geopandas support, we'll need the following wheels
rem geopandas dependencies downloaded from https://www.lfd.uci.edu/~gohlke/pythonlibs/
rem note: Fiona install requires GDAL to be on the path
setlocal
set WHEELS_PATH=%~dp0\bin\wheels
pip install %WHEELS_PATH%\Rtree-0.9.3-cp27-cp27m-win_amd64.whl
pip install %WHEELS_PATH%\pyproj-1.9.6-cp27-cp27m-win_amd64.whl
pip install %WHEELS_PATH%\GDAL-2.2.4-cp27-cp27m-win_amd64.whl
pip install %WHEELS_PATH%\Fiona-1.8.13-cp27-cp27m-win_amd64.whl
rem pip install %WHEELS_PATH%\Rtree-0.9.3-cp27-cp27m-win_amd64.whl
rem pip install %WHEELS_PATH%\pyproj-1.9.6-cp27-cp27m-win_amd64.whl
rem pip install %WHEELS_PATH%\GDAL-2.2.4-cp27-cp27m-win_amd64.whl
rem pip install %WHEELS_PATH%\Fiona-1.8.13-cp27-cp27m-win_amd64.whl

rem remaining dependencies are downloaded by pip
pip install -r requirements.txt

rem make available in Jupyter notebooks
python -m ipykernel install --user --name="Emme-RFMD"

rem Test that the venv is working
python -c "import inro.emme.desktop.app as _app"
python -c "import geopandas as gpd"

call deactivate
PAUSE
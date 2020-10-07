rem call using:
rem setup_emme_venv

c:\python37\python.exe -m pip install virtualenv
c:\python37\python.exe -m virtualenv .venv

call .venv\Scripts\activate.bat

rem Upgrade pip to latest
python -m pip install --upgrade pip

REM python bin/unzip_mod_spatialite.py

rem remaining dependencies are downloaded by pip
pip install -r requirements.txt

rem make available in Jupyter notebooks
python -m ipykernel install --user --name="VLC Notebooks"

call deactivate
PAUSE

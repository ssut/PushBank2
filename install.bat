@echo off
python -c "import sys;v=sys.version_info;sys.exit(0 if v>=(3,3) else 1)" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.3 이상이 설치되어있어야 합니다.
    goto :end
) else (
    echo Python 바이너리를 찾았습니다.
    goto :check_pip
)

:check_pip
where pip >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo pip가 설치되어있어야 합니다.
    echo 참고: https://pip.pypa.io/en/latest/installing.html
    goto :end
) else (
    echo pip를 찾았습니다.
    goto :install
)

:install
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo 설치에 실패한 것 같습니다. 오류를 확인한 후 다시 설치해주세요.
    goto :end
) else (
    goto :done 
)

:done
move config_sample.json config.json >nul 2>nul
copy NUL start.bat >nulc
echo @echo off > start.bat
echo python pushbank >> start.bat
echo pause >> start.bat
echo config.json 파일을 가이드라인에 맞춰 수정한 후 start.bat로 실행하세요.
pause >nul

:end
exit 0

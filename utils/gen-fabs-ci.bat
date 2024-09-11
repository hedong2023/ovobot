@echo off
chcp 65001
@REM cd to script directory
pushd "%~dp0"
setlocal enableextensions enabledelayedexpansion

set args=%*

for %%a in (%args%) do (
    for /F "tokens=1,2 delims=\\" %%i in ("%%a") do (
        if exist ..\fabs\%%i (
            rmdir /s /q ..\fabs\%%i
        )
    )
)

for %%a in (%args%) do (
    for /F "tokens=1,2 delims=\\" %%i in ("%%a") do (
        echo:
        echo Generate %%i %%j fabrication outputs
        call :gen %%i %%j
    )
)

endlocal
popd
exit /b

:gen
for /F "tokens=1-2* delims=-" %%a in ("%2") do (
    set brd=%%c
)

@REM 获取Board版本
for /F "tokens=1-2* delims=###" %%a in ('python get-brd-revision.py ..\%1\%2\%2.kicad_pcb') do (
    set ver=%%a
    set brdSize=%%b
    set brdLayerCnt=%%c
)

echo %ver%
echo %brdSize%
echo 板子层数：%brdLayerCnt%

set outdir=..\fabs\%1\%1-%brd%-%ver%
set gerber=%outdir%\%1-%brd%-%ver%-Gerber
set posfile=%outdir%\%1-%brd%-%ver%-Pos.csv
set jlcposfile=%outdir%\%1-%brd%-%ver%-Pos-jlc.csv
set bomfile=%outdir%\%1-%brd%-%ver%-Bom.xlsx
set jlcbomfile=%outdir%\%1-%brd%-%ver%-Bom-jlc.xlsx
set smtT=%outdir%\%1-%brd%-%ver%-Fab-Top.pdf
set smtB=%outdir%\%1-%brd%-%ver%-Fab-Bottom.pdf

mkdir %gerber%

@REM gen bom
echo Generate bom
kicad-cli sch export python-bom -o bom.xml ..\%1\%2\%2.kicad_sch
python bom_csv_grouped_by_value_with_fp_no_nc.py "bom.xml" "..\%1\%2\%2.json" "%brdSize%" "%bomfile%"
if defined opt if "%opt%"=="jlc" (
    python bom_csv_grouped_by_value_with_fp_no_nc_jlc.py "bom.xml" "..\%1\%2\%2.json" "%brdSize%" "%jlcbomfile%"
)
del bom.xml

@REM gen gerbers and drill
echo Generate gerber and drill
set layers=F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts
if %brdLayerCnt%==4 set layers=%layers%,In1.Cu,In2.Cu,
if %brdLayerCnt%==6 set layers=%layers%,In1.Cu,In2.Cu,In3.Cu,In4.Cu,
kicad-cli pcb export gerbers  -o %gerber%  -l %layers% --cl Edge.Cuts ..\%1\%2\%2.kicad_pcb
kicad-cli pcb export drill  -o %gerber%/ ..\%1\%2\%2.kicad_pcb

@REM gen pos file
echo Generate position file
kicad-cli pcb export pos --format csv --units mm --use-drill-file-origin -o %posfile% ..\%1\%2\%2.kicad_pcb
if defined opt if "%opt%"=="jlc" (
    python gen-jlc-pos.py %posfile% %jlcposfile%
)

@REM gen pdf
echo Generate fabrication pdf
kicad-cli pcb export pdf -o %smtT% -l F.Fab,Edge.Cuts --black-and-white ..\%1\%2\%2.kicad_pcb
kicad-cli pcb export pdf -o %smtB% -l B.Fab,B.Courtyard,Edge.Cuts -m --black-and-white ..\%1\%2\%2.kicad_pcb
exit /b
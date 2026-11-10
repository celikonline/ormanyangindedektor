@echo off
rem ON-1 saf mantik birim testleri - Windows
rem Sirasiyla g++ (MSYS2/MinGW), clang++ ve MSVC cl denenir.
setlocal
cd /d "%~dp0"
set SRC=..\OrmanNobetcisi
set FILES=test_logic.cpp %SRC%\storage.cpp %SRC%\textutil.cpp %SRC%\detector.cpp %SRC%\commands.cpp

where g++ >nul 2>nul && (
  g++ -std=c++11 -O1 -Wall -Wextra -Wno-unused-parameter -I%SRC% -o test_logic.exe %FILES% || exit /b 1
  goto run
)
where clang++ >nul 2>nul && (
  clang++ -std=c++11 -O1 -Wall -Wextra -Wno-unused-parameter -I%SRC% -o test_logic.exe %FILES% || exit /b 1
  goto run
)
where cl >nul 2>nul && (
  cl /nologo /EHsc /W3 /I%SRC% /Fe:test_logic.exe %FILES% || exit /b 1
  goto run
)
echo C++ derleyici bulunamadi (g++ / clang++ / cl). Node.js yedegi: node test_logic.mjs
exit /b 2

:run
test_logic.exe
exit /b %ERRORLEVEL%

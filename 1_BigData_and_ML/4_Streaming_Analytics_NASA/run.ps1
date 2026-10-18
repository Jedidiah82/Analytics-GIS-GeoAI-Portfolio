param(
    [Parameter(Mandatory=$true)][string]$JulyLog,
    [Parameter(Mandatory=$true)][string]$AugustLog,
    [string]$Python='python',
    [string]$PrivateDirectory=(Join-Path $PSScriptRoot 'private-replay')
)
$ErrorActionPreference='Stop'
$runtimeTemp=Join-Path $PSScriptRoot '.runtime-temp'
New-Item -ItemType Directory -Force -Path $runtimeTemp | Out-Null
$env:TEMP=$runtimeTemp
$env:TMP=$runtimeTemp
$env:PYSPARK_PYTHON=(& $Python -c 'import sys; print(sys.executable)')
$env:PYSPARK_DRIVER_PYTHON=$env:PYSPARK_PYTHON
$env:SPARK_HOME=(& $Python -c 'import pathlib,pyspark; print(pathlib.Path(pyspark.__file__).parent)')
$env:PYSPARK_SUBMIT_ARGS='--driver-memory 4g pyspark-shell'
if ($env:HADOOP_HOME) { $env:PATH=(Join-Path $env:HADOOP_HOME 'bin')+';'+$env:PATH }
& $Python (Join-Path $PSScriptRoot 'notebooks_or_src/prepare_replay.py') --sources $JulyLog $AugustLog --private-dir $PrivateDirectory
if ($LASTEXITCODE -ne 0) { throw 'Input preparation failed. Use a fresh private directory and inspect the error.' }
& $Python -m unittest discover -s (Join-Path $PSScriptRoot 'tests') -v
if ($LASTEXITCODE -ne 0) { throw 'Parser tests failed.' }
& $Python (Join-Path $PSScriptRoot 'notebooks_or_src/test_stream_contract.py') --private-dir (Join-Path $PrivateDirectory 'contracts') --project $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Streaming contract tests failed.' }
& $Python (Join-Path $PSScriptRoot 'notebooks_or_src/run_replay.py') --private-dir $PrivateDirectory --project $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Replay or count reconciliation failed.' }
& $Python (Join-Path $PSScriptRoot 'notebooks_or_src/plot_results.py') --project $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Figure generation failed.' }

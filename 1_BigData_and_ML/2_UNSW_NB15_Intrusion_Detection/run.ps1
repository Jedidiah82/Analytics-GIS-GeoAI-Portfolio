param(
    [Parameter(Mandatory=$true)][string]$InputCsv,
    [string]$Python='python',
    [string]$Master='local[4]'
)
$ErrorActionPreference='Stop'
# Keep temporary files inside this project; configure JAVA_HOME for Java 11.
$projectRoot=$PSScriptRoot
$runtimeTemp=Join-Path $projectRoot '.runtime-temp'
New-Item -ItemType Directory -Force -Path $runtimeTemp | Out-Null
$env:TEMP=$runtimeTemp
$env:TMP=$runtimeTemp
$env:PYSPARK_PYTHON=(& $Python -c 'import sys; print(sys.executable)')
$env:PYSPARK_DRIVER_PYTHON=$env:PYSPARK_PYTHON
$env:SPARK_HOME=(& $Python -c 'import pathlib,pyspark; print(pathlib.Path(pyspark.__file__).parent)')
$env:PYSPARK_SUBMIT_ARGS='--driver-memory 6g pyspark-shell'
& $Python (Join-Path $projectRoot 'src/unsw_model_workflow.py') --input $InputCsv --output $projectRoot --private-output (Join-Path $projectRoot 'private-predictions') --master $Master
if ($LASTEXITCODE -ne 0) { throw 'Model evaluation failed; inspect the error before publishing results.' }
& $Python (Join-Path $projectRoot 'src/export_full_curves.py') --project $projectRoot --private-predictions (Join-Path $projectRoot 'private-predictions')
if ($LASTEXITCODE -ne 0) { throw 'Full curve export failed.' }
& $Python (Join-Path $projectRoot 'src/plot_results.py') --project $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Figure generation failed.' }

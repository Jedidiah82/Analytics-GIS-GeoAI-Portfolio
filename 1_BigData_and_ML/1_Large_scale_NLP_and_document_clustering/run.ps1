param([Parameter(Mandatory=$true)][string]$News,[Parameter(Mandatory=$true)][string]$Groups,[string]$Python='python')
$ErrorActionPreference='Stop'
$env:PYTHONHASHSEED='42'
& $Python -m unittest discover -s "$PSScriptRoot/tests" -v
if ($LASTEXITCODE -ne 0) {throw 'Tests failed'}
& $Python "$PSScriptRoot/src/run_experiments.py" --news $News --groups $Groups --output "$PSScriptRoot/results" --private "$PSScriptRoot/private-results"
if ($LASTEXITCODE -ne 0) {throw 'Experiments failed'}
& $Python "$PSScriptRoot/src/validate_results.py" --results "$PSScriptRoot/results"
if ($LASTEXITCODE -ne 0) {throw 'Result reconciliation failed'}
& $Python "$PSScriptRoot/src/plot_results.py" --results "$PSScriptRoot/results" --figures "$PSScriptRoot/figures"
if ($LASTEXITCODE -ne 0) {throw 'Figures failed'}

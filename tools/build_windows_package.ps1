[CmdletBinding()]
param(
    [string] $PackageName = "russian-catalog-localizer-desktop-v0.2.0-windows",
    [string] $OutDir = "release",
    [switch] $NoZip,
    [switch] $SkipExeBuild,
    [switch] $SkipSmoke
)

$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $PSCommandPath
$RepoRoot = Resolve-Path (Join-Path $ToolsDir "..")
$RepoRoot = $RepoRoot.ProviderPath

if ([System.IO.Path]::IsPathRooted($OutDir)) {
    throw "OutDir must be a repository-relative folder, for example: release"
}

if ($PackageName -match '[\\/]' -or $PackageName -in @(".", "..")) {
    throw "PackageName must be a single folder name, not a path."
}

$ReleaseRoot = Join-Path $RepoRoot $OutDir
$PackageDir = Join-Path $ReleaseRoot $PackageName
$ZipPath = Join-Path $ReleaseRoot "$PackageName.zip"
$BuildRoot = Join-Path $RepoRoot "build"
$PyInstallerDist = Join-Path $BuildRoot "pyinstaller-dist"
$PyInstallerWork = Join-Path $BuildRoot "pyinstaller-work"
$PyInstallerSpec = Join-Path $BuildRoot "pyinstaller-spec"
$ExeBuildPath = Join-Path $PyInstallerDist "RussianCatalogLocalizer.exe"
$ExeName = "CatalogLocalizer.exe"
$PackageExe = Join-Path $PackageDir $ExeName

function Copy-RequiredItem {
    param(
        [Parameter(Mandatory = $true)]
        [string] $RelativePath,
        [Parameter(Mandatory = $true)]
        [string] $DestinationRoot
    )

    $source = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Required item is missing: $RelativePath"
    }

    $destination = Join-Path $DestinationRoot $RelativePath
    $destinationParent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}

function Write-PackageReadme {
    param(
        [Parameter(Mandatory = $true)]
        [string] $DestinationPath
    )

    $content = @(
        '# Russian Catalog Localizer Desktop'
        ''
        '## Start'
        ''
        '1. Extract this folder.'
        '2. Double-click `CatalogLocalizer.exe`.'
        '3. Click the Chinese `Run Demo` button in the app.'
        '4. For real data, select OCR JSON, glossary CSV, and an output folder.'
        ''
        '## What this version does'
        ''
        '- Reads OCR JSON segments.'
        '- Applies a Chinese-to-Russian glossary.'
        '- Writes `segments.ru.json`, `repaint_plan.json`, and `qa_report.md`.'
        '- Packages sanitized output as `localized_package.zip`.'
        ''
        '## Current limitation'
        ''
        'This version does not directly OCR a PDF or render a final localized PDF.'
        ''
        '## Output files'
        ''
        '- `segments.ru.json`: localized text segments.'
        '- `repaint_plan.json`: working repaint plan for downstream rendering.'
        '- `qa_report.md`: working residual Chinese QA report.'
        '- `localized_package.zip`: sanitized package for sharing.'
        ''
        'The working files may contain source OCR text. Share `localized_package.zip` only after checking the QA report.'
    )

    Set-Content -LiteralPath $DestinationPath -Value $content -Encoding UTF8
}

function Get-PyInstallerTkArgs {
    $probeScript = @'
import json
import os
import sys

base = sys.base_prefix
items = {"binaries": [], "datas": []}
candidate_dll_dirs = [
    os.path.join(base, "DLLs"),
    os.path.join(base, "Library", "bin"),
]
for name in ("tcl86t.dll", "tk86t.dll"):
    for dll_dir in candidate_dll_dirs:
        path = os.path.join(dll_dir, name)
        if os.path.exists(path):
            items["binaries"].append([path, "."])
            break

candidate_tcl_roots = [
    os.path.join(base, "tcl"),
    os.path.join(base, "Library", "lib"),
]
for tcl_root in candidate_tcl_roots:
    for name in ("tcl8.6", "tk8.6"):
        path = os.path.join(tcl_root, name)
        if os.path.isdir(path) and [path, os.path.join("tcl", name)] not in items["datas"]:
            items["datas"].append([path, os.path.join("tcl", name)])

print(json.dumps(items))
'@

    $probePath = Join-Path $PyInstallerWork "probe_tk_runtime.py"
    Set-Content -LiteralPath $probePath -Value $probeScript -Encoding UTF8
    try {
        $probeOutput = python $probePath
        if ($LASTEXITCODE -ne 0) {
            throw "Could not inspect Python Tcl/Tk runtime."
        }
    } finally {
        Remove-Item -LiteralPath $probePath -Force -ErrorAction SilentlyContinue
    }

    $tkItems = $probeOutput | ConvertFrom-Json
    $args = @("--hidden-import", "tkinter", "--hidden-import", "_tkinter")

    foreach ($binary in @($tkItems.binaries)) {
        $args += @("--add-binary", "$($binary[0]);$($binary[1])")
    }
    foreach ($data in @($tkItems.datas)) {
        $args += @("--add-data", "$($data[0]);$($data[1])")
    }

    if (@($tkItems.binaries).Count -lt 2) {
        Write-Warning "Could not find both Tcl/Tk DLLs under the active Python runtime. PyInstaller hooks may still collect them."
    } else {
        Write-Host "Including Tcl/Tk DLLs from the active Python runtime."
    }

    return $args
}

function Get-ProcessOutputTail {
    param(
        [string] $Path,
        [int] $LineCount = 80
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    return (Get-Content -LiteralPath $Path -Tail $LineCount) -join [Environment]::NewLine
}

function Invoke-PyInstallerBuild {
    if ($SkipExeBuild) {
        Write-Host "Skipping PyInstaller build."
        return
    }

    if (Test-Path -LiteralPath $PyInstallerDist) {
        Remove-Item -LiteralPath $PyInstallerDist -Recurse -Force
    }
    if (Test-Path -LiteralPath $PyInstallerWork) {
        Remove-Item -LiteralPath $PyInstallerWork -Recurse -Force
    }
    if (Test-Path -LiteralPath $PyInstallerSpec) {
        Remove-Item -LiteralPath $PyInstallerSpec -Recurse -Force
    }
    New-Item -ItemType Directory -Path $PyInstallerDist -Force | Out-Null
    New-Item -ItemType Directory -Path $PyInstallerWork -Force | Out-Null
    New-Item -ItemType Directory -Path $PyInstallerSpec -Force | Out-Null

    $entry = Join-Path $ToolsDir "desktop_entry.py"
    $srcPath = Join-Path $RepoRoot "src"
    $sampleSegmentsData = "$(Join-Path $RepoRoot 'src\russian_catalog_localizer\examples\sample_ocr_segments.json');russian_catalog_localizer\examples"
    $sampleGlossaryData = "$(Join-Path $RepoRoot 'src\russian_catalog_localizer\examples\glossary.zh-ru.csv');russian_catalog_localizer\examples"

    $tkArgs = Get-PyInstallerTkArgs
    $pyInstallerArgs = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "RussianCatalogLocalizer",
        "--paths", "$srcPath",
        "--add-data", "$sampleSegmentsData",
        "--add-data", "$sampleGlossaryData",
        "--distpath", "$PyInstallerDist",
        "--workpath", "$PyInstallerWork",
        "--specpath", "$PyInstallerSpec"
    ) + $tkArgs + @("$entry")

    $env:PYTHONPATH = "$srcPath;$env:PYTHONPATH"
    python @pyInstallerArgs

    if (-not (Test-Path -LiteralPath $ExeBuildPath)) {
        throw "PyInstaller did not create expected executable: $ExeBuildPath"
    }
}

function Test-Smoke {
    if ($SkipSmoke) {
        Write-Host "Skipping package smoke test."
        return
    }

    $smokeDir = Join-Path $ReleaseRoot "_smoke"
    if (Test-Path -LiteralPath $smokeDir) {
        Remove-Item -LiteralPath $smokeDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $smokeDir -Force | Out-Null

    $stdoutLog = Join-Path $ReleaseRoot "_smoke_stdout.log"
    $stderrLog = Join-Path $ReleaseRoot "_smoke_stderr.log"
    Remove-Item -LiteralPath $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $PackageExe
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    $escapedSmokeDir = $smokeDir -replace '"', '\"'
    $startInfo.Arguments = "--demo-out `"$escapedSmokeDir`""

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void] $process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    Set-Content -LiteralPath $stdoutLog -Value $stdout -Encoding UTF8
    Set-Content -LiteralPath $stderrLog -Value $stderr -Encoding UTF8

    if ($process.ExitCode -ne 0) {
        $stdoutTail = Get-ProcessOutputTail -Path $stdoutLog
        $stderrTail = Get-ProcessOutputTail -Path $stderrLog
        throw "Packaged executable smoke test failed with exit code $($process.ExitCode).`nSTDOUT:`n$stdoutTail`nSTDERR:`n$stderrTail"
    }

    $expected = @("segments.ru.json", "repaint_plan.json", "qa_report.md", "localized_package.zip")
    foreach ($name in $expected) {
        $path = Join-Path $smokeDir $name
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Smoke output is missing: $name"
        }
    }

    $qaText = Get-Content -LiteralPath (Join-Path $smokeDir "qa_report.md") -Raw
    if ($qaText -notmatch "Residual Chinese hits: 0") {
        throw "Smoke QA did not pass residual Chinese check."
    }

    Remove-Item -LiteralPath $smokeDir -Recurse -Force
    Write-Host "Smoke stdout: $stdoutLog"
    Write-Host "Smoke stderr: $stderrLog"
}

Write-Host "Building desktop customer package..."
Write-Host "Repository: $RepoRoot"
Write-Host "Package:    $PackageDir"

Invoke-PyInstallerBuild

if (Test-Path -LiteralPath $PackageDir) {
    Remove-Item -LiteralPath $PackageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

Copy-Item -LiteralPath $ExeBuildPath -Destination $PackageExe -Force
Copy-Item -LiteralPath (Join-Path $ToolsDir "run_app.bat") -Destination (Join-Path $PackageDir "run_app.bat") -Force

$requiredItems = @(
    "examples\sample_ocr_segments.json",
    "examples\glossary.zh-ru.csv",
    "configs",
    "README.md",
    "LICENSE",
    "docs\customer-quick-start.zh-CN.md"
)

foreach ($item in $requiredItems) {
    Copy-RequiredItem -RelativePath $item -DestinationRoot $PackageDir
}

Write-PackageReadme -DestinationPath (Join-Path $PackageDir "README.customer.md")
New-Item -ItemType Directory -Path (Join-Path $PackageDir "output") -Force | Out-Null

Test-Smoke

if (-not $NoZip) {
    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force
    Write-Host "Wrote zip: $ZipPath"
}

Write-Host "Wrote folder: $PackageDir"
Write-Host "Executable: $PackageExe"
Write-Host "Smoke test: passed"

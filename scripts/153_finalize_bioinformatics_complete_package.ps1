param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$source = Join-Path $rootPath "submission_package_bioinformatics_final_doi"
$dest = Join-Path $rootPath "submission_package_bioinformatics_complete"
$codeRoot = Join-Path $dest "Supplementary_Code"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem -LiteralPath $source | Where-Object {
    $_.Name -notin @(
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS_Final.txt",
        "Submission_Check_Final.json",
        "Submission_Check_Final.md"
    )
} | Copy-Item -Destination $dest -Recurse

Copy-Item -LiteralPath (Join-Path $rootPath "release_artifacts/Zenodo_DOIs.json") -Destination (Join-Path $codeRoot "RATA_Zenodo_DOIs.json")

$oldCodeZip = Join-Path $dest "RATA_Bioinformatics_Supplementary_Code.zip"
$newCodeZip = Join-Path $dest "RATA_Bioinformatics_Supplementary_Code_v2.zip"
Compress-Archive -LiteralPath $codeRoot -DestinationPath $newCodeZip -CompressionLevel Optimal

Get-ChildItem -LiteralPath $dest -File | Where-Object { $_.Name -ne "RATA_Bioinformatics_Supplementary_Code_v2.zip" } | Select-Object Name,Length | Format-Table -AutoSize

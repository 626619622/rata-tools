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
        "RATA_Bioinformatics_Supplementary_Code.zip",
        "SHA256SUMS_Final.txt",
        "Submission_Check_Final.json",
        "Submission_Check_Final.md"
    )
} | Copy-Item -Destination $dest -Recurse

Copy-Item -LiteralPath (Join-Path $rootPath "release_artifacts/Zenodo_DOIs.json") -Destination (Join-Path $codeRoot "RATA_Zenodo_DOIs.json")

$codeZip = Join-Path $dest "RATA_Bioinformatics_Supplementary_Code.zip"
Compress-Archive -LiteralPath $codeRoot -DestinationPath $codeZip -CompressionLevel Optimal

$staging = Get-ChildItem -LiteralPath $dest | Where-Object {
    $_.Name -notin @("RATA_Bioinformatics_Submission_Package.zip", "SHA256SUMS_Final.txt")
}
$packageZip = Join-Path $dest "RATA_Bioinformatics_Submission_Package.zip"
Compress-Archive -LiteralPath $staging.FullName -DestinationPath $packageZip -CompressionLevel Optimal

$manifest = Join-Path $dest "SHA256SUMS_Final.txt"
$files = Get-ChildItem -LiteralPath $dest -File | Where-Object { $_.Name -ne "SHA256SUMS_Final.txt" }
$files += Get-ChildItem -LiteralPath (Join-Path $dest "Figures") -File
$lines = foreach ($file in $files | Sort-Object FullName) {
    $relative = $file.FullName.Substring($dest.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0}  {1}" -f $hash,$relative
}
$lines | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $dest | Select-Object Name,Length,Mode | Format-Table -AutoSize

param(
    [Parameter(Mandatory = $false)]
    [string]$Package = "codex_output/endocrine-transport-project/submission_package_bioinformatics_v3"
)

$ErrorActionPreference = "Stop"
$packagePath = (Resolve-Path -LiteralPath $Package).Path
$zip = Join-Path $packagePath "RATA_Bioinformatics_Submission_Package.zip"
if (Test-Path -LiteralPath $zip) {
    throw "Refusing to overwrite existing package archive: $zip"
}

$staging = Get-ChildItem -LiteralPath $packagePath | Where-Object {
    $_.Name -notin @(
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS_Final.txt"
    )
}
$paths = $staging.FullName
Compress-Archive -LiteralPath $paths -DestinationPath $zip -CompressionLevel Optimal

$manifest = Join-Path $packagePath "SHA256SUMS_Final.txt"
$files = Get-ChildItem -LiteralPath $packagePath -File | Where-Object {
    $_.Name -ne "SHA256SUMS_Final.txt"
}
$files += Get-ChildItem -LiteralPath (Join-Path $packagePath "Figures") -File
$lines = foreach ($file in $files | Sort-Object FullName) {
    $relative = $file.FullName.Substring($packagePath.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0}  {1}" -f $hash,$relative
}
$lines | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $packagePath -File | Select-Object Name,Length | Format-Table -AutoSize

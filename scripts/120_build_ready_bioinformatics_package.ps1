param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$source = Join-Path $rootPath "submission_package_bioinformatics_v4"
$dest = Join-Path $rootPath "submission_package_bioinformatics_ready"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem -LiteralPath $source | Where-Object {
    $_.Name -notin @(
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS_Final.txt",
        "Submission_Check_Final.json",
        "Submission_Check_Final.md",
        "README_SUBMISSION.md"
    )
} | Copy-Item -Destination $dest -Recurse

Copy-Item -LiteralPath (Join-Path $rootPath "Bioinformatics_Submission_README_v2.md") -Destination (Join-Path $dest "README_SUBMISSION.md")
Copy-Item -LiteralPath (Join-Path $source "Submission_Check_Final.json") -Destination (Join-Path $dest "Submission_Check_Final.json")
Copy-Item -LiteralPath (Join-Path $source "Submission_Check_Final.md") -Destination (Join-Path $dest "Submission_Check_Final.md")

$zip = Join-Path $dest "RATA_Bioinformatics_Submission_Package.zip"
$staging = Get-ChildItem -LiteralPath $dest | Where-Object {
    $_.Name -notin @("RATA_Bioinformatics_Submission_Package.zip", "SHA256SUMS_Final.txt")
}
Compress-Archive -LiteralPath $staging.FullName -DestinationPath $zip -CompressionLevel Optimal

$manifest = Join-Path $dest "SHA256SUMS_Final.txt"
$files = Get-ChildItem -LiteralPath $dest -File | Where-Object {
    $_.Name -ne "SHA256SUMS_Final.txt"
}
$files += Get-ChildItem -LiteralPath (Join-Path $dest "Figures") -File
$lines = foreach ($file in $files | Sort-Object FullName) {
    $relative = $file.FullName.Substring($dest.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0}  {1}" -f $hash,$relative
}
$lines | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $dest | Select-Object Name,Length,Mode | Format-Table -AutoSize

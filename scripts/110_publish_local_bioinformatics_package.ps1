param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$source = Join-Path $rootPath "submission_package_bioinformatics_v3"
$dest = Join-Path $rootPath "submission_package_bioinformatics_final"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem -LiteralPath $source | Where-Object {
    $_.Name -notin @(
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS.txt",
        "SHA256SUMS_Final.txt",
        "Submission_Check_Final.json",
        "Submission_Check_Final.md"
    )
} | Copy-Item -Destination $dest -Recurse

$admin = Join-Path $rootPath "manuscript/lo_admin"
Copy-Item -LiteralPath (Join-Path $admin "RATA_Bioinformatics_TitlePage_v1.pdf") -Destination (Join-Path $dest "RATA_Bioinformatics_TitlePage.pdf")
Copy-Item -LiteralPath (Join-Path $admin "RATA_Bioinformatics_CoverLetter_v1.pdf") -Destination (Join-Path $dest "RATA_Bioinformatics_CoverLetter.pdf")
Copy-Item -LiteralPath (Join-Path $admin "RATA_Bioinformatics_SoftwareAvailability.pdf") -Destination (Join-Path $dest "RATA_Bioinformatics_SoftwareAvailability.pdf")
Copy-Item -LiteralPath (Join-Path $source "Submission_Check_Final.md") -Destination (Join-Path $dest "Submission_Check_Final.md")
Copy-Item -LiteralPath (Join-Path $source "Submission_Check_Final.json") -Destination (Join-Path $dest "Submission_Check_Final.json")

$zip = Join-Path $dest "RATA_Bioinformatics_Submission_Package.zip"
$staging = Get-ChildItem -LiteralPath $dest | Where-Object {
    $_.Name -notin @(
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS_Final.txt"
    )
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

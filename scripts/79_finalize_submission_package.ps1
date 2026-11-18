param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$package = Join-Path $rootPath "submission_package_final"
$figOut = Join-Path $package "Figures"
New-Item -ItemType Directory -Force -Path $package,$figOut | Out-Null

$manuscript = Join-Path $rootPath "manuscript"
$figures = Join-Path $rootPath "figures/paper1"

Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_Manuscript_v6.docx") -Destination (Join-Path $package "RATA_Paper1_Manuscript.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "lo_render_check/RATA_Paper1_Manuscript_v6.pdf") -Destination (Join-Path $package "RATA_Paper1_Manuscript.pdf")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_TitlePage_v2.docx") -Destination (Join-Path $package "RATA_Paper1_TitlePage.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_CoverLetter_v2.docx") -Destination (Join-Path $package "RATA_Paper1_CoverLetter.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_Supplementary_v3.pdf") -Destination (Join-Path $package "RATA_Paper1_Supplementary.pdf")
Copy-Item -LiteralPath (Join-Path $rootPath "Submission_Package_README.md") -Destination (Join-Path $package "README_SUBMISSION.md")
Copy-Item -LiteralPath (Join-Path $rootPath "submission_package_v1/RATA_Paper1_Submission_Check_Final.md") -Destination (Join-Path $package "RATA_Paper1_Submission_Check_Final.md")

Copy-Item -LiteralPath (Join-Path $figures "Figure1_evidence_capacity.pdf") -Destination (Join-Path $figOut "Figure1.pdf")
Copy-Item -LiteralPath (Join-Path $figures "Figure2_selection_gate.pdf") -Destination (Join-Path $figOut "Figure2.pdf")
Copy-Item -LiteralPath (Join-Path $figures "Figure3_transport_and_role_adjustment.pdf") -Destination (Join-Path $figOut "Figure3.pdf")
Copy-Item -LiteralPath (Join-Path $figures "Figure4_pituitary_positive_control.pdf") -Destination (Join-Path $figOut "Figure4.pdf")
Copy-Item -LiteralPath (Join-Path $figures "Figure5_invasion_and_operating_characteristics_v2.pdf") -Destination (Join-Path $figOut "Figure5.pdf")

Copy-Item -LiteralPath (Join-Path $figures "Figure1_evidence_capacity.png") -Destination (Join-Path $figOut "Figure1.png")
Copy-Item -LiteralPath (Join-Path $figures "Figure2_selection_gate.png") -Destination (Join-Path $figOut "Figure2.png")
Copy-Item -LiteralPath (Join-Path $figures "Figure3_transport_and_role_adjustment.png") -Destination (Join-Path $figOut "Figure3.png")
Copy-Item -LiteralPath (Join-Path $figures "Figure4_pituitary_positive_control.png") -Destination (Join-Path $figOut "Figure4.png")
Copy-Item -LiteralPath (Join-Path $figures "Figure5_invasion_and_operating_characteristics_v2.png") -Destination (Join-Path $figOut "Figure5.png")
Copy-Item -LiteralPath (Join-Path $figures "ContactSheet_v2.png") -Destination (Join-Path $package "Figure_ContactSheet.png")

$codeSource = Join-Path $rootPath "submission_package_v1/Supplementary_Code"
$zip = Join-Path $package "RATA_Paper1_Supplementary_Code.zip"
Compress-Archive -LiteralPath $codeSource -DestinationPath $zip -CompressionLevel Optimal

$manifest = Join-Path $package "SHA256SUMS_Final.txt"
$files = Get-ChildItem -LiteralPath $package -File | Where-Object { $_.Name -ne "SHA256SUMS_Final.txt" }
$files += Get-ChildItem -LiteralPath $figOut -File
$lines = foreach ($file in $files | Sort-Object FullName) {
    $relative = $file.FullName.Substring($package.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0}  {1}" -f $hash,$relative
}
$lines | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $package | Select-Object Name,Length,Mode | Format-Table -AutoSize

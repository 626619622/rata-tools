param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$package = Join-Path $rootPath "submission_package_v1"
$codeRoot = Join-Path $package "Supplementary_Code"
$figOut = Join-Path $package "Figures"

New-Item -ItemType Directory -Force -Path $package,$codeRoot,$figOut | Out-Null

$manuscript = Join-Path $rootPath "manuscript"
$figures = Join-Path $rootPath "figures/paper1"

Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_Manuscript_v6.docx") -Destination (Join-Path $package "RATA_Paper1_Manuscript.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "lo_render_check/RATA_Paper1_Manuscript_v6.pdf") -Destination (Join-Path $package "RATA_Paper1_Manuscript.pdf")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_TitlePage_v2.docx") -Destination (Join-Path $package "RATA_Paper1_TitlePage.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_CoverLetter_v2.docx") -Destination (Join-Path $package "RATA_Paper1_CoverLetter.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_Supplementary_v3.pdf") -Destination (Join-Path $package "RATA_Paper1_Supplementary.pdf")

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

$codeScripts = Join-Path $codeRoot "scripts"
New-Item -ItemType Directory -Force -Path $codeScripts | Out-Null
Get-ChildItem -LiteralPath (Join-Path $rootPath "scripts") -File |
    Where-Object {
        $number = 0
        [int]::TryParse(($_.BaseName -split "_")[0], [ref]$number) -and
        $number -ge 27 -and $number -le 76
    } |
    Copy-Item -Destination $codeScripts

Copy-Item -LiteralPath (Join-Path $rootPath "results") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "registry") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "locks") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "rata_package") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "Method_RATA_ThreeGate_v3.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "PreRegistration_RATA_PredictiveValidity_v2.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "PreRegistration_RATA_ThirdDisease_SBNET_v1.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "Supplementary_Code_README.md") -Destination (Join-Path $codeRoot "README.md")

$manuscriptArchive = Join-Path $codeRoot "manuscript"
New-Item -ItemType Directory -Force -Path $manuscriptArchive | Out-Null
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper1_Manuscript_v6.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $figures "Figure1_evidence_capacity_v2.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $figures "Figure2_selection_gate_v2.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $figures "Figure3_transport_and_role_adjustment.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $figures "Figure4_pituitary_positive_control.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $figures "Figure5_invasion_and_operating_characteristics_v2.md") -Destination $manuscriptArchive

$zip = Join-Path $package "RATA_Paper1_Supplementary_Code.zip"
if (Test-Path -LiteralPath $zip) {
    throw "Refusing to overwrite existing archive: $zip"
}
Compress-Archive -LiteralPath $codeRoot -DestinationPath $zip -CompressionLevel Optimal

$manifest = Join-Path $package "SHA256SUMS.txt"
Get-ChildItem -LiteralPath $package -File |
    Where-Object { $_.Name -ne "SHA256SUMS.txt" } |
    Sort-Object Name |
    ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "{0}  {1}" -f $hash,$_.Name
    } | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $package -File | Select-Object Name,Length | Format-Table -AutoSize

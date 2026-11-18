param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$package = Join-Path $rootPath "submission_package_bioinformatics_v3"
$figOut = Join-Path $package "Figures"
$codeRoot = Join-Path $package "Supplementary_Code"
$softwareOut = Join-Path $codeRoot "software"

New-Item -ItemType Directory -Force -Path $package,$figOut,$codeRoot,$softwareOut | Out-Null

$manuscript = Join-Path $rootPath "manuscript"
$figures = Join-Path $rootPath "figures/bioinformatics_final"
$release = Join-Path $rootPath "rata_tools_release_0.2.0"

Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper_Bioinformatics_v3.docx") -Destination (Join-Path $package "RATA_Bioinformatics_Manuscript.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "lo_bioinformatics_v3/RATA_Paper_Bioinformatics_v3.pdf") -Destination (Join-Path $package "RATA_Bioinformatics_Manuscript.pdf")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_TitlePage_v1.docx") -Destination (Join-Path $package "RATA_Bioinformatics_TitlePage.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_CoverLetter_v1.docx") -Destination (Join-Path $package "RATA_Bioinformatics_CoverLetter.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_SoftwareAvailability.docx") -Destination (Join-Path $package "RATA_Bioinformatics_SoftwareAvailability.docx")
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_Supplementary_v1.pdf") -Destination (Join-Path $package "RATA_Bioinformatics_Supplementary.pdf")
Copy-Item -LiteralPath (Join-Path $rootPath "Bioinformatics_Submission_README.md") -Destination (Join-Path $package "README_SUBMISSION.md")
Copy-Item -LiteralPath (Join-Path $rootPath "Release_Action_Required.md") -Destination (Join-Path $package "Release_Action_Required.md")
Copy-Item -LiteralPath (Join-Path $rootPath "release_artifacts/RATA_ACC_registry_v1.0.0.zip") -Destination (Join-Path $package "RATA_ACC_registry_v1.0.0.zip")

for ($i = 1; $i -le 6; $i++) {
    Copy-Item -LiteralPath (Join-Path $figures "Figure$i.pdf") -Destination (Join-Path $figOut "Figure$i.pdf")
    Copy-Item -LiteralPath (Join-Path $figures "Figure$i.png") -Destination (Join-Path $figOut "Figure$i.png")
    Copy-Item -LiteralPath (Join-Path $figures "Figure$i.md") -Destination (Join-Path $figOut "Figure$i.md")
}
Copy-Item -LiteralPath (Join-Path $figures "Figure_ContactSheet.png") -Destination (Join-Path $package "Figure_ContactSheet.png")

Copy-Item -LiteralPath (Join-Path $release "src") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release "tests") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release "docs") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release "examples") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release "dist") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release ".github") -Destination $softwareOut -Recurse
Copy-Item -LiteralPath (Join-Path $release "pyproject.toml") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release "README.md") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release "LICENSE") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release "CHANGELOG.md") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release "CITATION.cff") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release "MANIFEST.in") -Destination $softwareOut
Copy-Item -LiteralPath (Join-Path $release ".zenodo.json") -Destination $softwareOut

$scriptOut = Join-Path $codeRoot "scripts"
New-Item -ItemType Directory -Force -Path $scriptOut | Out-Null
Get-ChildItem -LiteralPath (Join-Path $rootPath "scripts") -File |
    Where-Object {
        $number = 0
        [int]::TryParse(($_.BaseName -split "_")[0], [ref]$number) -and
        $number -ge 27 -and $number -le 107
    } |
    Copy-Item -Destination $scriptOut

Copy-Item -LiteralPath (Join-Path $rootPath "results") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "registry") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "locks") -Destination $codeRoot -Recurse
Copy-Item -LiteralPath (Join-Path $rootPath "Method_RATA_ThreeGate_v3.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "PreRegistration_RATA_PredictiveValidity_v2.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "PreRegistration_RATA_ThirdDisease_SBNET_v1.md") -Destination $codeRoot
Copy-Item -LiteralPath (Join-Path $rootPath "Supplementary_Code_README_v2.md") -Destination (Join-Path $codeRoot "README.md")

$manuscriptArchive = Join-Path $codeRoot "manuscript"
New-Item -ItemType Directory -Force -Path $manuscriptArchive | Out-Null
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Paper_Bioinformatics_v7.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_TitlePage_v1.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_CoverLetter_v1.md") -Destination $manuscriptArchive
Copy-Item -LiteralPath (Join-Path $manuscript "RATA_Bioinformatics_SoftwareAvailability.md") -Destination $manuscriptArchive
Get-ChildItem -LiteralPath $figures -Filter "Figure*.md" | Copy-Item -Destination $manuscriptArchive

$zip = Join-Path $package "RATA_Bioinformatics_Supplementary_Code.zip"
Compress-Archive -LiteralPath $codeRoot -DestinationPath $zip -CompressionLevel Optimal

$manifest = Join-Path $package "SHA256SUMS.txt"
$files = Get-ChildItem -LiteralPath $package -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" }
$files += Get-ChildItem -LiteralPath $figOut -File
$lines = foreach ($file in $files | Sort-Object FullName) {
    $relative = $file.FullName.Substring($package.Length).TrimStart('\')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "{0}  {1}" -f $hash,$relative
}
$lines | Set-Content -LiteralPath $manifest -Encoding ascii

Get-ChildItem -LiteralPath $package | Select-Object Name,Length,Mode | Format-Table -AutoSize

param(
    [Parameter(Mandatory = $false)]
    [string]$Source = "C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final",
    [Parameter(Mandatory = $false)]
    [string]$Revision = "codex_output\endocrine-transport-project\cmpb_submission_20261118"
)

$ErrorActionPreference = "Stop"
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$revisionPath = (Resolve-Path -LiteralPath $Revision).Path
$package = Join-Path $revisionPath "CMPB_Submission_v3"
New-Item -ItemType Directory -Force -Path $package | Out-Null

Copy-Item -LiteralPath (Join-Path $revisionPath "RATA_CMPB_Manuscript_v3.docx") -Destination (Join-Path $package "RATA_CMPB_Manuscript_v3.docx")
Copy-Item -LiteralPath (Join-Path $revisionPath "render/RATA_CMPB_Manuscript_v3.pdf") -Destination (Join-Path $package "RATA_CMPB_Manuscript_v3.pdf")
Copy-Item -LiteralPath (Join-Path $revisionPath "references_verified_v3.md") -Destination (Join-Path $package "references_verified.md")
Copy-Item -LiteralPath (Join-Path $revisionPath "SUBMISSION_CHECKLIST_v3.md") -Destination (Join-Path $package "SUBMISSION_CHECKLIST.md")
Copy-Item -LiteralPath (Join-Path $revisionPath "Gate1_Final_Lock.md") -Destination (Join-Path $package "Gate1_Final_Lock.md")
Copy-Item -LiteralPath (Join-Path $revisionPath "RATA_v5_double_null_selection_gate_final.csv") -Destination (Join-Path $package "RATA_v5_double_null_selection_gate_final.csv")
Copy-Item -LiteralPath (Join-Path $revisionPath "RATA_v5_double_null_selection_gate_final.json") -Destination (Join-Path $package "RATA_v5_double_null_selection_gate_final.json")
Copy-Item -LiteralPath (Join-Path $revisionPath "reference_identifier_resolution_v3.md") -Destination (Join-Path $package "reference_identifier_resolution.md")
Copy-Item -LiteralPath (Join-Path $revisionPath "citation_coverage_v2.md") -Destination (Join-Path $package "citation_coverage.md")
Copy-Item -LiteralPath (Join-Path $revisionPath "RATA_CMPB_Status_v3.md") -Destination (Join-Path $package "RATA_CMPB_Status_v3.md")

Copy-Item -LiteralPath (Join-Path $sourcePath "RATA_CMPB_CoverLetter.docx") -Destination (Join-Path $package "RATA_CMPB_CoverLetter.docx")
Copy-Item -LiteralPath (Join-Path $sourcePath "figures") -Destination $package -Recurse

$zip = Join-Path $revisionPath "RATA_CMPB_Submission_v3.zip"
if (Test-Path -LiteralPath $zip) {
    throw "Refusing to overwrite existing archive: $zip"
}
Compress-Archive -LiteralPath $package -DestinationPath $zip -CompressionLevel Optimal

Get-ChildItem -LiteralPath $package | Select-Object Name,Length,Mode | Format-Table -AutoSize
Write-Output $zip

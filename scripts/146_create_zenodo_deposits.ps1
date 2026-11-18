param(
    [Parameter(Mandatory = $false)]
    [string]$Root = "codex_output/endocrine-transport-project"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$token = (Get-Clipboard -Raw)
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Clipboard does not contain a Zenodo token."
}
$token = $token.Trim()
if ($token.Length -lt 20 -or $token -match "\s") {
    throw "Clipboard does not contain a single Zenodo token."
}

$baseHeaders = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/json"
    "User-Agent" = "RATA-Zenodo-Deposit/1.0"
}
$jsonHeaders = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/json"
    "Content-Type" = "application/json"
    "User-Agent" = "RATA-Zenodo-Deposit/1.0"
}
$fileHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/octet-stream"
    "User-Agent" = "RATA-Zenodo-Deposit/1.0"
}

function New-ZenodoDeposit {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][hashtable]$Metadata,
        [Parameter(Mandatory = $true)][string]$FilePath
    )

    $deposit = Invoke-RestMethod `
        -Uri "https://zenodo.org/api/deposit/depositions" `
        -Headers $jsonHeaders `
        -Method Post `
        -Body "{}" `
        -TimeoutSec 60
    $depositId = $deposit.id
    $bucket = $deposit.links.bucket
    $fileName = Split-Path -Leaf $FilePath
    Invoke-WebRequest `
        -Uri "$bucket/$fileName" `
        -Headers $fileHeaders `
        -Method Put `
        -InFile $FilePath `
        -UseBasicParsing `
        -TimeoutSec 300 | Out-Null

    $body = @{ metadata = $Metadata } | ConvertTo-Json -Depth 12
    Invoke-RestMethod `
        -Uri "https://zenodo.org/api/deposit/depositions/$depositId" `
        -Headers $jsonHeaders `
        -Method Put `
        -Body $body `
        -TimeoutSec 60 | Out-Null
    $published = Invoke-RestMethod `
        -Uri "https://zenodo.org/api/deposit/depositions/$depositId/actions/publish" `
        -Headers $jsonHeaders `
        -Method Post `
        -Body "{}" `
        -TimeoutSec 120
    if (-not $published.doi) {
        throw "Zenodo published deposit $depositId without a DOI."
    }
    return [pscustomobject]@{
        id = $depositId
        title = $Title
        doi = $published.doi
        url = $published.links.html
        file = $fileName
    }
}

try {
    $existing = Invoke-RestMethod `
        -Uri "https://zenodo.org/api/deposit/depositions" `
        -Headers $baseHeaders `
        -Method Get `
        -TimeoutSec 60
    Write-Output "Zenodo authentication: PASS"
    Write-Output "Existing deposition count: $($existing.Count)"

    $softwareFile = Join-Path $rootPath "submission_package_bioinformatics_public/RATA_Bioinformatics_Supplementary_Code.zip"
    $registryFile = Join-Path $rootPath "release_artifacts/RATA_ACC_registry_v1.0.0.zip"
    if (-not (Test-Path -LiteralPath $softwareFile)) {
        throw "Software archive missing: $softwareFile"
    }
    if (-not (Test-Path -LiteralPath $registryFile)) {
        throw "Registry archive missing: $registryFile"
    }

    $creator = @(
        @{
            name = "Zhao, Jiakang"
            affiliation = "Zhongda Hospital, Southeast University"
            orcid = "0009-0006-4878-0626"
        }
    )
    $softwareMetadata = @{
        title = "rata-tools: Role-Aware Transportability Audit primitives"
        upload_type = "software"
        publication_date = "2026-11-12"
        description = "<p>rata-tools 0.2.0 provides reusable Python primitives for auditing the transportability of transcriptomic signatures. It implements evidence-capacity metrics, selection-aware cross-validation, matched selection-null decisions, binary and cohort-stratified survival transport gates, Harrell C-index utilities and structured three-gate decisions. The release includes a Python API, command-line interface, tests, examples, documentation and continuous-integration configuration.</p>"
        creators = $creator
        version = "0.2.0"
        license = "mit"
        keywords = @(
            "transportability",
            "external validation",
            "transcriptomics",
            "evidence audit",
            "reproducible software"
        )
        related_identifiers = @(
            @{
                identifier = "https://github.com/626619622/rata-tools/releases/tag/v0.2.0"
                relation = "isSupplementTo"
                resource_type = "software"
                scheme = "url"
            }
        )
    }
    $software = New-ZenodoDeposit `
        -Title $softwareMetadata.title `
        -Metadata $softwareMetadata `
        -FilePath $softwareFile
    Write-Output "Software DOI: $($software.doi)"

    $registryMetadata = @{
        title = "RATA ACC signature-cohort provenance registry"
        upload_type = "dataset"
        publication_date = "2026-11-12"
        description = "<p>Pair-level provenance registry and evidence-capacity tables for 11 published adrenocortical carcinoma transcriptomic signatures. The registry records cohort reuse, platforms, endpoints, events, independence grades and reuse clusters used in the RATA transportability audit.</p>"
        creators = $creator
        version = "1.0.0"
        license = "cc-by-4.0"
        keywords = @(
            "adrenocortical carcinoma",
            "provenance",
            "signature validation",
            "cohort reuse",
            "evidence capacity"
        )
        related_identifiers = @(
            @{
                identifier = $software.doi
                relation = "isSupplementTo"
                resource_type = "software"
                scheme = "doi"
            }
        )
    }
    $registry = New-ZenodoDeposit `
        -Title $registryMetadata.title `
        -Metadata $registryMetadata `
        -FilePath $registryFile
    Write-Output "Registry DOI: $($registry.doi)"

    $result = [ordered]@{
        software = $software
        registry = $registry
        created_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    $resultPath = Join-Path $rootPath "release_artifacts/Zenodo_DOIs.json"
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Output "Saved DOI manifest: $resultPath"
} finally {
    $token = $null
    Set-Clipboard -Value ""
}

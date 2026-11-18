param(
    [Parameter(Mandatory = $false)]
    [string]$TokenPath = "codex_output/endocrine-transport-project/.secrets/zenodo_token.secure"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $TokenPath)) {
    throw "Encrypted token not found: $TokenPath"
}

$encrypted = Get-Content -Raw -LiteralPath $TokenPath
$secure = ConvertTo-SecureString -String $encrypted
$credential = [System.Management.Automation.PSCredential]::new("zenodo", $secure)
$token = $credential.GetNetworkCredential().Password
$headers = @{
    "Authorization" = "Bearer $token"
    "User-Agent" = "RATA-Zenodo-Deposit/1.0"
    "Accept" = "application/json"
}
try {
    $response = Invoke-RestMethod -Uri "https://zenodo.org/api/deposit/depositions" -Headers $headers -Method Get -TimeoutSec 30
    Write-Output "Zenodo token authentication: PASS"
    Write-Output "Existing deposition count: $($response.Count)"
} finally {
    $token = $null
    $credential = $null
    $secure.Dispose()
}

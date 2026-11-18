param(
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "codex_output/endocrine-transport-project/.secrets/zenodo_token.secure"
)

$ErrorActionPreference = "Stop"
$secure = Read-Host "Paste the Zenodo personal access token (input is hidden)" -AsSecureString
if ($secure.Length -eq 0) {
    throw "No token entered."
}

$directory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$encrypted = ConvertFrom-SecureString -SecureString $secure
Set-Content -LiteralPath $OutputPath -Value $encrypted -Encoding ascii
Write-Output "Encrypted token saved to: $OutputPath"
Write-Output "The token is protected with Windows DPAPI for the current user."

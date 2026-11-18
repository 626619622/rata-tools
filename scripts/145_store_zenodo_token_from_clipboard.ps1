param(
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "codex_output/endocrine-transport-project/.secrets/zenodo_token.secure"
)

$ErrorActionPreference = "Stop"
$tokenText = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($tokenText)) {
    throw "Clipboard is empty. Copy the Zenodo token first."
}
$tokenText = $tokenText.Trim()
if ($tokenText.Length -lt 20 -or $tokenText -match "\s") {
    throw "Clipboard does not look like a single Zenodo access token."
}

$secure = ConvertTo-SecureString -String $tokenText -AsPlainText -Force
$directory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$encrypted = ConvertFrom-SecureString -SecureString $secure
Set-Content -LiteralPath $OutputPath -Value $encrypted -Encoding ascii
Set-Clipboard -Value ""

$secure.Dispose()
$tokenText = $null
Write-Output "Zenodo token encrypted and stored for the current Windows user."
Write-Output "Clipboard cleared."

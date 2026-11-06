param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [int]$Width=1280,
    [int]$Height=720
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "PPTX not found: $Source" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$app=New-Object -ComObject PowerPoint.Application
try {
    $deck=$app.Presentations.Open($Source,-1,0,0)
    try {
        for ($i=1; $i -le $deck.Slides.Count; $i++) {
            $file=Join-Path $OutputDir ('slide-{0:D2}.png' -f $i)
            $deck.Slides.Item($i).Export($file,'PNG',$Width,$Height)
            Write-Output $file
        }
    } finally { $deck.Close() }
} finally { $app.Quit() }

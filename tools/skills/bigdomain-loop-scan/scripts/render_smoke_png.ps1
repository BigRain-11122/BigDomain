# render_smoke_png.ps1 - render a QA smoke log to a PNG evidence image.
# Group QA Smoke Test charter (docs/qa-smoke-test-charter.md v1.0, orders L254 2026-09-28):
# evidence image must be derived from the REAL log, never hand-drawn or fabricated.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File render_smoke_png.ps1 <log> <png> [max_lines]
# ASCII-only script per repo encoding law; log content is rendered verbatim (non-ASCII -> '?').
param(
  [Parameter(Mandatory = $true)][string]$LogPath,
  [Parameter(Mandatory = $true)][string]$PngPath,
  [int]$MaxLines = 80
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$lines = @(Get-Content -LiteralPath $LogPath -Encoding UTF8 | Select-Object -First $MaxLines)
if ($lines.Count -eq 0) { throw "empty log: $LogPath" }

$font = New-Object System.Drawing.Font('Consolas', 12)
$fmt = [System.Drawing.StringFormat]::GenericTypographic

# measure pass
$probe = New-Object System.Drawing.Bitmap(4, 4)
$g = [System.Drawing.Graphics]::FromImage($probe)
$lineH = $font.GetHeight($g)
$maxW = 0.0
foreach ($l in $lines) {
  $txt = ($l -replace '[^\x00-\x7F]', '?')
  if ($txt.Length -eq 0) { $txt = ' ' }
  $sz = $g.MeasureString($txt, $font, [int]::MaxValue, $fmt)
  if ($sz.Width -gt $maxW) { $maxW = $sz.Width }
}
$g.Dispose(); $probe.Dispose()

$w = [int]([Math]::Min($maxW + 24, 1880))
$h = [int]([Math]::Max($lines.Count * ($lineH + 3) + 24, 400))
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::FromArgb(16, 16, 20))

$plain = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(225, 225, 225))
$accent = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(120, 220, 140))
$head = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(120, 170, 255))
$y = 12.0
for ($i = 0; $i -lt $lines.Count; $i++) {
  $txt = ($lines[$i] -replace '[^\x00-\x7F]', '?')
  if ($txt.Length -eq 0) { $txt = ' ' }
  $b = $plain
  if ($i -eq 0) { $b = $head }
  elseif ($txt -match '^\[\d\].*: (PASS|FAIL)') { $b = $accent }
  elseif ($txt -match '^\[|^self-judge|HIT$|-> HIT') { $b = $accent }
  $g.DrawString($txt, $font, $b, 12.0, $y, $fmt)
  $y += $lineH + 3
}
$g.Dispose()
$bmp.Save($PngPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output ("rendered " + $PngPath + " lines=" + $lines.Count + " size=" + $w + "x" + $h)

# BigDomain ygo interop PoC runner (ASCII only per repo encoding rule).
# Uses a portable Go toolchain in %TEMP%\bd-ygo-poc (sha256-verified, no
# system install) because this host has no Docker and no system Go.
# Node.js is required on PATH (repo host has v24).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue' # Expand-Archive/Invoke-WebRequest progress rendering is 10x slower
$PoCRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PoCRoot

# ---- stage 0: portable Go toolchain bootstrap (idempotent) ----
# Toolchain lives in-repo under gitignored data\toolchain because a temp-dir
# cleaner/AV wiped go.exe out of %TEMP% mid-run on this host (2026-10-08).
$TR = Join-Path $PoCRoot 'data\toolchain'
$GOROOT = Join-Path $TR 'goroot'
$goexe = Join-Path $GOROOT 'bin\go.exe'
if (-not (Test-Path $goexe)) {
  New-Item -ItemType Directory -Path $TR -Force | Out-Null
  $zip = Join-Path $TR 'go1.26.8.windows-amd64.zip'
  if (-not (Test-Path $zip)) {
    Invoke-WebRequest -Uri 'https://golang.google.cn/dl/go1.26.8.windows-amd64.zip' -OutFile $zip -UseBasicParsing
  }
  $h = (Get-FileHash -Path $zip -Algorithm SHA256).Hash
  if ($h -ne 'B92C3B2ADAE85A11BA71FE7216DAF0D84E82AF4C8AB6C5625807F28622043A59') { throw 'sha256 mismatch for go zip' }
  Expand-Archive -Path $zip -DestinationPath $TR -Force
  if (Test-Path $GOROOT) { Remove-Item -Recurse -Force $GOROOT }
  Rename-Item -Path (Join-Path $TR 'go') -NewName 'goroot'
}
$env:GOROOT = $GOROOT
$env:GOPATH = Join-Path $TR 'gopath'
$env:GOCACHE = Join-Path $TR 'gocache'
$env:GOMODCACHE = Join-Path $env:GOPATH 'pkg\mod'
$env:GOTMPDIR = Join-Path $TR 'gotmp' # host %TEMP% blocks new-dir creation by go.exe (Access denied, 2026-10-08)
New-Item -ItemType Directory -Path $env:GOTMPDIR -Force | Out-Null
$env:GOPROXY = 'https://goproxy.cn,direct'
$env:PATH = "$GOROOT\bin;$env:PATH"
Write-Host ('STAGE0 toolchain: ' + (& $goexe version))

# ---- stage 1: js deps ----
Push-Location js
if (-not (Test-Path 'node_modules')) { & npm.cmd install --no-audit --no-fund }
if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'npm install failed' }
Pop-Location

# ---- stage 2: generate yjs fixtures ----
& node js\gen-fixtures.mjs
if ($LASTEXITCODE -ne 0) { throw 'fixture generation failed' }

# ---- stage 3: go harness ----
Push-Location go-interop
& $goexe mod tidy
if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'go mod tidy failed' }
& $goexe run .
if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'go harness failed (AC-YG1/YG3-pre/YG5-pre)' }
Pop-Location

# ---- stage 4: js verify of go outputs ----
& node js\verify-reply.mjs
if ($LASTEXITCODE -ne 0) { throw 'AC-YG2..YG5 verification failed' }

# ---- stage 5: yserve transport tests ----
# AC-YG6a/b (pre-registered, @hocuspocus/provider 2.15.3): FAIL by root cause,
# recorded honestly, not skipped - yserve v1.22.0 implements the bare
# y-websocket envelope only (docName = URL path; tags 0/1/3; no docName
# prefix), while the provider speaks the multi-doc Hocuspocus envelope
# (every message prefixed with the document name). yserve silently drops the
# provider's frames, so 'synced' never fires. AC-YG6b (provider persistence)
# is untestable through the same broken handshake: phase1 never writes state.
# AC-YG6c/d (supplementary, added after root-cause 2026-10-08): the same
# live-convergence + persistence claims through the y-websocket envelope
# (js/client-yws.mjs), the protocol yserve actually documents and supports.
New-Item -ItemType Directory -Path data -Force | Out-Null
$yserve = Join-Path $PoCRoot 'data\yserve.exe'
if (-not (Test-Path $yserve)) { # idempotent skip: relink is a multi-minute silent stretch; exe built by this exact pinned command (2026-10-08 07:50)
  & $goexe install github.com/Deln0r/ygo/cmd/yserve@v1.22.0
  if ($LASTEXITCODE -ne 0) { throw 'go install yserve failed' }
}
$db = Join-Path $PoCRoot 'data\yserve-poc.db'
if (Test-Path $db) { Remove-Item -Force $db }

function Start-Yserve {
  # Redirect child stdio to files: without this, the console child inherits the
  # invoking session's stdout pipe and tool sessions hang on handle closure
  # (observed 2026-10-08: two cancelled 5-min runs at the same wall).
  $p = Start-Process -FilePath $yserve -ArgumentList @('-addr', '127.0.0.1:1987', '-store', $db) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PoCRoot 'data\yserve-serve.log') -RedirectStandardError (Join-Path $PoCRoot 'data\yserve-err.log') -PassThru
  $ok = $false
  foreach ($i in 1..40) {
    Start-Sleep -Milliseconds 250
    try {
      $c = New-Object Net.Sockets.TcpClient
      $c.Connect('127.0.0.1', 1987)
      $c.Close()
      $ok = $true
      break
    } catch {}
  }
  if (-not $ok) { throw 'yserve did not listen on 127.0.0.1:1987' }
  return $p
}

$ys1 = Start-Yserve
try {
  & node js\client-yserve.mjs phase1
  if ($LASTEXITCODE -eq 0) {
    Write-Host 'AC-YG6a (@hocuspocus/provider): PASS - UNEXPECTED, protocol analysis said FAIL; re-examine'
  } else {
    Write-Host 'AC-YG6a (@hocuspocus/provider): FAIL - yserve drops the Hocuspocus multi-doc envelope (root cause in README/oh notes)'
  }
} finally { Stop-Process -Id $ys1.Id -Force -ErrorAction SilentlyContinue }

$ys2 = Start-Yserve
try {
  & node js\client-yws.mjs phase1
  if ($LASTEXITCODE -ne 0) { throw 'AC-YG6c live convergence (y-websocket envelope) failed' }
} finally { Stop-Process -Id $ys2.Id -Force -ErrorAction SilentlyContinue }

$ys3 = Start-Yserve
try {
  & node js\client-yws.mjs phase2
  if ($LASTEXITCODE -ne 0) { throw 'AC-YG6d persistence (y-websocket envelope) failed' }
} finally { Stop-Process -Id $ys3.Id -Force -ErrorAction SilentlyContinue }

Write-Host 'POC RESULT: AC-YG1..YG5 PASS (wire-compat core); AC-YG6a/b FAIL (Hocuspocus provider envelope unsupported); AC-YG6c/d PASS (y-websocket envelope)'
exit 1 # pre-registered suite incomplete: AC-YG6a/b FAIL is an honest mixed verdict, not a crash

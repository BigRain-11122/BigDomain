# run-trial.ps1 - BigDomain face of Ternary-Bonsai fleet trial (ASCII-only script; prompts live in samples.json)
# Candidate: llama-server 127.0.0.1:8077 (Ternary-Bonsai-2-27B-PTQ1_0, CPU tier)
# Baseline : Ollama 127.0.0.1:11434 OpenAI-compat (qwen2.5:7b-instruct-q8_0)
# Outputs  : per-sample raw resp JSON + content txt + summary.json (citation-grade evidence)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Get-Content -LiteralPath (Join-Path $here 'samples.json') -Encoding UTF8 | ConvertFrom-Json

$endpoints = @(
    @{ id = 'bonsai'; url = 'http://127.0.0.1:8077/v1/chat/completions'; model = 'ternary-bonsai-2-27b'; thinkingOff = $true },
    @{ id = 'qwen7b';  url = 'http://127.0.0.1:11434/v1/chat/completions'; model = 'qwen2.5:7b-instruct-q8_0'; thinkingOff = $false }
)

$summary = @()
foreach ($s in $data.samples) {
    foreach ($ep in $endpoints) {
        $bodyObj = @{
            model = $ep.model
            messages = @(
                @{ role = 'system'; content = $data.meta.system_prompt },
                @{ role = 'user';   content = $s.brief }
            )
            max_tokens = $s.max_tokens
            temperature = 0.7
            stream = $false
        }
        if ($ep.thinkingOff) { $bodyObj.chat_template_kwargs = @{ enable_thinking = $false } }
        $bodyJson = $bodyObj | ConvertTo-Json -Depth 6
        $tmp = Join-Path $env:TEMP ("bd-trial-" + $s.id + "-" + $ep.id + ".json")
        [System.IO.File]::WriteAllText($tmp, $bodyJson, (New-Object System.Text.UTF8Encoding($false)))

        $t0 = Get-Date
        $outFile = Join-Path $here ("resp-" + $s.id + "-" + $ep.id + ".json")
        & curl.exe -s -m 600 -X POST $ep.url -H "Content-Type: application/json" --data-binary "@$tmp" -o $outFile
        $t1 = Get-Date
        $resp = Get-Content -LiteralPath $outFile -Encoding UTF8 -Raw | ConvertFrom-Json
        $content = ''
        if ($resp.choices -and $resp.choices.Count -gt 0) { $content = [string]$resp.choices[0].message.content }
        [System.IO.File]::WriteAllText((Join-Path $here ("out-" + $s.id + "-" + $ep.id + ".txt")), $content, (New-Object System.Text.UTF8Encoding($false)))

        $lat = [math]::Round(($t1 - $t0).TotalSeconds, 1)
        $ct = 0; $pt = 0; $finish = 'n/a'
        if ($resp.usage) { $ct = [int]$resp.usage.completion_tokens; $pt = [int]$resp.usage.prompt_tokens }
        if ($resp.choices -and $resp.choices[0].finish_reason) { $finish = [string]$resp.choices[0].finish_reason }
        $tps = 0
        if ($ct -gt 0 -and $lat -gt 0) { $tps = [math]::Round($ct / $lat, 2) }
        $summary += [pscustomobject]@{
            sample = $s.id; kind = $s.kind; endpoint = $ep.id
            latency_s = $lat; prompt_tok = $pt; completion_tok = $ct; tok_per_s = $tps; finish = $finish
        }
        Write-Host ("{0} {1}: {2}s ct={3} tps={4} finish={5}" -f $s.id, $ep.id, $lat, $ct, $tps, $finish)
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    }
}
$summary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $here 'summary.json') -Encoding UTF8
Write-Host 'DONE summary.json written'

param(
  [string]$J0 = "http://localhost:2358",
  [string]$Token = $env:JUDGE0_AUTH_TOKEN
)
if (-not $Token) { $Token = "local-dev-token-abc123" }

$ErrorActionPreference = "Continue"
$H = @{ 'X-Auth-Token' = $Token; 'Content-Type' = 'application/json' }

# Gửi bài rồi poll theo token thay vì `wait=true`.
# Lý do: với bài Time Limit Exceeded, `wait=true` của image mrkushalsm/judge0:cgv2
# đôi khi treo vô hạn dù Judge0 đã chấm xong. Backend cũng dùng poll
# (xem backend/app/modules/submissions/judge0/judge0_client.py) nên cách này khớp với production hơn.
function Submit($name, $body, $b64 = $false) {
  $qs = if ($b64) { "base64_encoded=true" } else { "base64_encoded=false" }
  try {
    $created = Invoke-RestMethod -Method Post -Uri "$J0/submissions?$qs" -Headers $H -Body $body -TimeoutSec 60
    $tok = $created.token

    $r = $null
    for ($i = 0; $i -lt 60; $i++) {
      Start-Sleep -Milliseconds 700
      $r = Invoke-RestMethod -Uri "$J0/submissions/$tok" -Headers $H -TimeoutSec 30
      # status 1 = In Queue, 2 = Processing
      if ($r.status.id -notin 1, 2) { break }
    }

    if ($null -eq $r -or $r.status.id -in 1, 2) {
      "{0,-22} TIMEOUT (still {1})" -f $name, $r.status.description
      return
    }

    $status = $r.status.description
    $time = $r.time
    $mem = $r.memory
    $detail = ""
    if ($status -match "Compilation Error") {
      if ($b64 -and $r.compile_output) {
        $detail = ($r.compile_output -replace '\s','')
        try { $detail = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($detail)).Split("`n")[0] } catch {}
      }
    } elseif ($status -eq "Wrong Answer") {
      $detail = "got='$($r.stdout)' want='$($r.expected_output)'"
    } elseif ($status -eq "Runtime Error (NZEC)") {
      $detail = "stderr='$($r.stderr)' msg='$($r.message)'"
    } elseif ($status -eq "Time Limit Exceeded") {
      $detail = "cpu_time=$time"
    }
    "{0,-22} {1,-20} time={2,-7} mem={3,-8} {4}" -f $name, $status, $time, $mem, $detail
  } catch {
    "{0,-22} REQUEST FAILED: {1}" -f $name, $_.Exception.Message
  }
}

Write-Host "=== Judge0 verdict test ===" -ForegroundColor Cyan
Submit "1 Accepted (Py)"    '{"language_id":71,"source_code":"print(int(input())*2)","stdin":"21","expected_output":"42"}'
Submit "2 Wrong Answer (Py)" '{"language_id":71,"source_code":"print(int(input())+1)","stdin":"21","expected_output":"42"}'
Submit "3 TimeLimit (C++)"   '{"language_id":54,"source_code":"int main(){while(true){}}","cpu_time_limit":1}'

# Compile Error phai gui base64_encoded=true
$src = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("int main(){ return 0 }"))
Submit "4 CompileError (C++)" "{`"language_id`":54,`"source_code`":`"$src`"}" $true

Submit "5 RuntimeError (Py)" '{"language_id":71,"source_code":"print(1/0)"}'

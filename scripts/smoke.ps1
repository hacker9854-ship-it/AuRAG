[CmdletBinding()]
param(
    [string]$BaseUrl = $(if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "http://localhost:8000" }),
    [string]$Query = "What caused the P-101 seal failure and what action should be taken?",
    [int]$ScoreTimeoutSeconds = 300,
    [int]$ProviderRetryAttempts = 4,
    [switch]$SkipReadiness,
    [switch]$SkipMutatingChecks,
    [switch]$SkipScoreWait,
    [switch]$SkipProviderChecks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

function Invoke-JsonRequest {
    param(
        [ValidateSet("GET", "POST", "PATCH")][string]$Method,
        [string]$Path,
        [object]$Body
    )

    $uri = "$BaseUrl$Path"
    $parameters = @{
        Uri = $uri
        Method = $Method
        UseBasicParsing = $true
        TimeoutSec = 120
        ErrorAction = "Stop"
    }
    if ($PSBoundParameters.ContainsKey("Body")) {
        $parameters["ContentType"] = "application/json"
        $parameters["Body"] = $Body | ConvertTo-Json -Depth 20 -Compress
    }

    $attempts = 1
    if ($Path -in @("/api/chat", "/api/comparison")) {
        $attempts = [Math]::Max(1, $ProviderRetryAttempts)
    }

    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        try {
            $response = Invoke-WebRequest @parameters
            Assert-Condition ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) "$Method $uri returned HTTP $($response.StatusCode)."
            if ([string]::IsNullOrWhiteSpace($response.Content)) {
                return $null
            }
            return $response.Content | ConvertFrom-Json
        }
        catch {
            $detail = $_.Exception.Message
            $statusCode = $null
            if ($null -ne $_.Exception.Response) {
                try {
                    $statusCode = [int]$_.Exception.Response.StatusCode
                }
                catch {
                    # Older PowerShell response objects expose status differently.
                }
                try {
                    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                    $payload = $reader.ReadToEnd()
                    if ($payload) {
                        $detail = "$detail Response: $payload"
                    }
                }
                catch {
                    # Preserve the original HTTP error when the response body is unavailable.
                }
            }

            $transient = $statusCode -in @(429, 502, 503, 504) -or $detail -match "429|502|503|504|high demand|temporar"
            if ($attempt -lt $attempts -and $transient) {
                $delay = [Math]::Min(20, [Math]::Pow(2, $attempt))
                Write-Warning "$Method $uri hit a transient provider error; retrying in $delay second(s)."
                Start-Sleep -Seconds $delay
                continue
            }
            throw "$Method $uri failed after $attempt attempt(s). $detail"
        }
    }
}

Write-Step "Checking process liveness"
$live = Invoke-JsonRequest -Method GET -Path "/api/health/live"
Assert-Condition ($live.status -eq "alive") "Liveness response was not alive."

if (-not $SkipReadiness) {
    Write-Step "Checking dependency readiness"
    $ready = Invoke-JsonRequest -Method GET -Path "/api/health/ready"
    Assert-Condition ([bool]$ready.ready) "Readiness response was not ready."
}

Write-Step "Loading seeded equipment"
$equipmentResponse = Invoke-JsonRequest -Method GET -Path "/api/equipment"
$equipment = @($equipmentResponse | ForEach-Object { $_ })
Assert-Condition ($equipment.Count -gt 0) "No equipment was returned. Run bootstrap with -InitializeData."
$equipmentTag = [string](($equipment | Select-Object -First 1).tag_id)
Assert-Condition ($equipmentTag -notmatch "\s") "Equipment response did not resolve to a single tag."

Write-Step "Checking knowledge-retirement risk"
$risk = Invoke-JsonRequest -Method GET -Path "/api/knowledge-risk?retirement_horizon=5"
Assert-Condition ($null -ne $risk.summary) "Knowledge-risk response did not include a summary."

Write-Step "Checking durable evaluation history"
$evaluations = Invoke-JsonRequest -Method GET -Path "/api/evaluations?limit=5"
$evaluationSummary = Invoke-JsonRequest -Method GET -Path "/api/evaluations/summary"
Assert-Condition ($null -ne $evaluations.items) "Evaluation history did not include items."
Assert-Condition ($null -ne $evaluationSummary.status_counts) "Evaluation summary did not include status counts."

Write-Step "Checking predictive-event history"
$notifications = Invoke-JsonRequest -Method GET -Path "/api/notifications?limit=5"
Assert-Condition ($null -ne $notifications.items) "Notification history did not include items."

if (-not $SkipProviderChecks) {
    Write-Step "Running grounded chat"
    $chat = Invoke-JsonRequest -Method POST -Path "/api/chat" -Body @{
        query = $Query
        user_id = "deployment-smoke"
        session_id = "deployment-smoke"
    }
    Assert-Condition (-not [string]::IsNullOrWhiteSpace([string]$chat.agent_response)) "Chat returned no answer."
    Assert-Condition (@($chat.citations).Count -gt 0) "Chat returned no citations."
    Assert-Condition (@($chat.graph_paths).Count -gt 0) "Chat returned no graph paths."

    Write-Step "Resolving connected graph evidence"
    $graph = Invoke-JsonRequest -Method POST -Path "/api/graph" -Body @{
        graph_paths = @($chat.graph_paths)
    }
    Assert-Condition (@($graph.nodes).Count -gt 0) "Graph evidence returned no nodes."
    Assert-Condition (@($graph.relationships).Count -gt 0) "Graph evidence returned no connected relationships."

    if ($chat.score_id) {
        Write-Step "Checking asynchronous scoring"
        $score = Invoke-JsonRequest -Method GET -Path "/api/chat/scores/$($chat.score_id)"
        if (-not $SkipScoreWait) {
            $deadline = [DateTime]::UtcNow.AddSeconds($ScoreTimeoutSeconds)
            while ($score.ragas_status -eq "scoring" -and [DateTime]::UtcNow -lt $deadline) {
                Start-Sleep -Seconds 2
                $score = Invoke-JsonRequest -Method GET -Path "/api/chat/scores/$($chat.score_id)"
            }
            Assert-Condition ($score.ragas_status -ne "scoring") "Scoring did not finish within $ScoreTimeoutSeconds seconds."
            Assert-Condition ($score.ragas_status -ne "error") "Scoring finished with an error: $($score.detail)"
        }
    }
    else {
        throw "Chat did not create a score job; retrieved context may be missing."
    }

    Write-Step "Running GraphRAG versus plain-RAG comparison"
    $comparison = Invoke-JsonRequest -Method POST -Path "/api/comparison" -Body @{ query = $Query }
    Assert-Condition ($null -ne $comparison.graph_rag) "Comparison omitted graph_rag."
    Assert-Condition ($null -ne $comparison.plain_rag) "Comparison omitted plain_rag."
    Assert-Condition ($null -ne $comparison.comparison_metrics) "Comparison omitted metrics."
}
else {
    Write-Host "Provider-backed chat, graph, scoring, and comparison checks skipped."
}

if (-not $SkipMutatingChecks) {
    Write-Warning "The remaining checks create a predictive event and a smoke-test work order, then reject that work order."

    Write-Step "Generating a high-drift telemetry event"
    $scan = Invoke-JsonRequest -Method POST -Path "/api/telemetry/scan" -Body @{
        equipment_tag = $equipmentTag
        drift_pct = 1.0
    }
    Assert-Condition (@($scan.matches).Count -gt 0) "Telemetry scan returned no failure matches for $equipmentTag."
    Assert-Condition ($null -ne $scan.warning) "High-drift telemetry did not produce a warning."
    $eventId = [string]$scan.warning.event_id
    Assert-Condition (-not [string]::IsNullOrWhiteSpace($eventId)) "Telemetry warning did not include an event ID."

    Write-Step "Verifying predictive-event deduplication"
    $repeatScan = Invoke-JsonRequest -Method POST -Path "/api/telemetry/scan" -Body @{
        equipment_tag = $equipmentTag
        drift_pct = 1.0
    }
    Assert-Condition ([string]$repeatScan.warning.event_id -eq $eventId) "Repeated scan did not reuse the predictive event ID."

    Write-Step "Confirming and acknowledging the predictive event"
    $eventHistory = Invoke-JsonRequest -Method GET -Path "/api/notifications?limit=200"
    $createdEvent = @($eventHistory.items | Where-Object { $_.id -eq $eventId })
    Assert-Condition ($createdEvent.Count -eq 1) "Created predictive event was not present in notification history."
    $readResult = Invoke-JsonRequest -Method POST -Path "/api/notifications/$eventId/read" -Body @{}
    Assert-Condition ($readResult.status -eq "read") "Predictive notification was not marked read."

    Write-Step "Creating, editing, and rejecting a work order"
    $draft = Invoke-JsonRequest -Method POST -Path "/api/telemetry/draft" -Body @{
        equipment_tag = $equipmentTag
        top_match = $scan.matches[0]
        event_id = $eventId
        actor = "deployment-smoke"
    }
    Assert-Condition ($draft.status -eq "Draft") "Work-order draft was not created in Draft status."
    $repeatDraft = Invoke-JsonRequest -Method POST -Path "/api/telemetry/draft" -Body @{
        equipment_tag = $equipmentTag
        top_match = $scan.matches[0]
        event_id = $eventId
        actor = "deployment-smoke"
    }
    Assert-Condition ($repeatDraft.id -eq $draft.id) "Repeated draft request did not reuse the work-order ID."

    $edited = Invoke-JsonRequest -Method PATCH -Path "/api/work-orders/$($draft.id)" -Body @{
        expected_version = [int]$draft.version
        description = "$($draft.description) [deployment smoke]"
        recommended_action = [string]$draft.recommended_action
        actor = "deployment-smoke"
    }
    Assert-Condition ($edited.status -eq "In Review") "Work-order edit did not move the record to In Review."

    $decided = Invoke-JsonRequest -Method POST -Path "/api/work-orders/$($draft.id)/decisions" -Body @{
        decision = "reject"
        expected_version = [int]$edited.version
        actor = "deployment-smoke"
        reason = "Automated deployment smoke record; no operational action required."
    }
    Assert-Condition ($decided.status -eq "Rejected") "Work-order rejection did not reach Rejected status."
}
else {
    Write-Host "Mutating telemetry, event acknowledgement, and work-order checks skipped."
}

Write-Step "Smoke checks passed"
Write-Host "Backend: $BaseUrl"
Write-Host "Equipment: $equipmentTag"
if (-not $SkipProviderChecks) {
    Write-Host "Chat score: $($chat.score_id)"
}

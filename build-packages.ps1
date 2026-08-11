# build-packages.ps1
# 一键打包 5 个工具的独立 zip 包
# 用法：在仓库根目录执行 .\build-packages.ps1

$ErrorActionPreference = "Stop"

$tools = @("zcode", "trae", "claude", "codex", "workbuddy")
$repoRoot = $PSScriptRoot
$distDir = Join-Path $repoRoot "dist"

# 清理并重建 dist 目录
if (Test-Path $distDir) {
    Remove-Item -Path $distDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $distDir | Out-Null

# 公共文件：scripts/ 和 LICENSE
$commonFiles = @(
    @{ Src = Join-Path $repoRoot "scripts"; Dst = "scripts" },
    @{ Src = Join-Path $repoRoot "LICENSE"; Dst = "LICENSE" }
)

foreach ($tool in $tools) {
    $adapterDir = Join-Path $repoRoot "adapters\$tool"
    $skillMd = Join-Path $adapterDir "SKILL.md"

    if (-not (Test-Path $skillMd)) {
        Write-Warning "跳过 $tool：找不到 $skillMd"
        continue
    }

    # 临时构建目录
    $buildDir = Join-Path $env:TEMP "see-glm-build-$tool"
    if (Test-Path $buildDir) {
        Remove-Item -Path $buildDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

    # 复制 SKILL.md
    Copy-Item -Path $skillMd -Destination $buildDir

    # 复制公共文件
    foreach ($f in $commonFiles) {
        Copy-Item -Path $f.Src -Destination (Join-Path $buildDir $f.Dst) -Recurse -Force
    }

    # Codex 和 zcode 额外打包 agents/openai.yaml
    if ($tool -in @("codex", "zcode")) {
        $agentsDir = Join-Path $repoRoot "agents"
        if (Test-Path $agentsDir) {
            $dstAgents = Join-Path $buildDir "agents"
            New-Item -ItemType Directory -Force -Path $dstAgents | Out-Null
            Copy-Item -Path (Join-Path $agentsDir "*") -Destination $dstAgents -Recurse -Force
        }
    }

    # 打包 zip
    $zipPath = Join-Path $distDir "see-glm-$tool.zip"
    if (Test-Path $zipPath) {
        Remove-Item -Path $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $buildDir "*") -DestinationPath $zipPath -Force

    # 清理临时目录
    Remove-Item -Path $buildDir -Recurse -Force

    $size = (Get-Item $zipPath).Length
    Write-Host "✓ see-glm-$tool.zip ($([math]::Round($size / 1KB, 1)) KB)" -ForegroundColor Green
}

Write-Host "`n=== 打包完成 ===" -ForegroundColor Cyan
Write-Host "输出目录: $distDir"
Get-ChildItem -Path $distDir | ForEach-Object {
    Write-Host "  $($_.Name) => $([math]::Round($_.Length / 1KB, 1)) KB"
}

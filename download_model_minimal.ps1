# Download ONLY required files (420MB total, not 2.82GB)

$baseUrl = "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main"
$outputDir = ".\data\models\paraphrase-multilingual-MiniLM-L12-v2"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Essential files only
$files = @(
  "pytorch_model.bin",
  "config.json",
  "tokenizer_config.json",
  "vocab.txt",
  "special_tokens_map.json",
  "tokenizer.json",
  "modules.json",
  "config_sentence_transformers.json"
)

Write-Host "Downloading essential files (~420MB total)" -ForegroundColor Green
Write-Host ""

$i = 1
foreach ($file in $files) {
  $url = "$baseUrl/$file"
  $output = Join-Path $outputDir $file

  Write-Host "[$i/$($files.Count)] $file" -ForegroundColor Yellow

  try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing -TimeoutSec 600
    Write-Host "  Downloaded" -ForegroundColor Green
  }
  catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
  }

  $i++
}

Write-Host ""
Write-Host "Download complete!" -ForegroundColor Green
Write-Host "Location: $outputDir" -ForegroundColor Cyan

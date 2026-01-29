# Download model files directly from HuggingFace
# Run this in PowerShell

$baseUrl = "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main"
$outputDir = ".\data\models\paraphrase-multilingual-MiniLM-L12-v2"

# Create directory
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# List of files to download
$files = @(
  "config.json",
  "tokenizer_config.json",
  "vocab.txt",
  "special_tokens_map.json",
  "tokenizer.json",
  "modules.json",
  "config_sentence_transformers.json",
  "sentence_bert_config.json",
  "pytorch_model.bin"  # 420MB - main file
)

Write-Host "Downloading model files to: $outputDir" -ForegroundColor Green

foreach ($file in $files) {
  $url = "$baseUrl/$file"
  $output = Join-Path $outputDir $file

  Write-Host "`nDownloading: $file" -ForegroundColor Yellow

  try {
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing -TimeoutSec 300
    Write-Host "✓ Downloaded: $file" -ForegroundColor Green
  }
  catch {
    Write-Host "✗ Failed: $file - $($_.Exception.Message)" -ForegroundColor Red
  }
}

Write-Host "`n✅ Download complete!" -ForegroundColor Green
Write-Host "Model location: $outputDir" -ForegroundColor Cyan

# Download model using aria2c (16 connections, faster)
# Install aria2c first: winget install aria2.aria2

$baseUrl = "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main"
$outputDir = ".\data\models\paraphrase-multilingual-MiniLM-L12-v2"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Main model file (420MB)
$url = "$baseUrl/pytorch_model.bin"
$output = Join-Path $outputDir "pytorch_model.bin"

Write-Host "Downloading pytorch_model.bin (420MB) with 16 connections..." -ForegroundColor Green
Write-Host "This should be much faster than single connection" -ForegroundColor Yellow

# Check if aria2c exists
if (Get-Command aria2c -ErrorAction SilentlyContinue) {
  aria2c -x 16 -s 16 -k 1M $url -d $outputDir -o "pytorch_model.bin"
}
else {
  Write-Host "aria2c not found. Install with: winget install aria2.aria2" -ForegroundColor Red
  Write-Host "Or use regular download (slower):" -ForegroundColor Yellow
  Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
}

# Download config files (small, fast)
$configs = @("config.json", "tokenizer_config.json", "vocab.txt", "special_tokens_map.json",
  "tokenizer.json", "modules.json", "config_sentence_transformers.json", "sentence_bert_config.json")

foreach ($file in $configs) {
  $url = "$baseUrl/$file"
  $out = Join-Path $outputDir $file
  Write-Host "Downloading $file..."
  Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction SilentlyContinue
}

Write-Host "`n✅ Download complete!" -ForegroundColor Green

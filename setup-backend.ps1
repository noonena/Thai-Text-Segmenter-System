# Thai Text Segmentation - Backend Setup (PowerShell)

Write-Host "🚀 Setting up Thai Text Segmentation Backend..." -ForegroundColor Cyan

# Create directory structure
Write-Host "`n📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path ".\backend\src\mtu" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\src\dictionary" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\src\word_segmentation" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\src\api" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\models" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\data\samples" -Force | Out-Null
New-Item -ItemType Directory -Path ".\backend\scripts" -Force | Out-Null

# Create __init__.py files
Write-Host "📝 Creating Python modules..." -ForegroundColor Yellow
$initFiles = @(
    ".\backend\src\__init__.py",
    ".\backend\src\mtu\__init__.py",
    ".\backend\src\dictionary\__init__.py",
    ".\backend\src\word_segmentation\__init__.py",
    ".\backend\src\api\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# Create .gitkeep files
Write-Host "🔖 Creating .gitkeep files..." -ForegroundColor Yellow
New-Item -ItemType File -Path ".\backend\models\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path ".\backend\data\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path ".\backend\data\samples\.gitkeep" -Force | Out-Null

Write-Host "`n✅ Backend structure created!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. cd backend"
Write-Host "2. python -m venv venv"
Write-Host "3. .\venv\Scripts\Activate.ps1"
Write-Host "4. pip install -r requirements.txt"
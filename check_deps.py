import importlib, subprocess

packages = [
    "boto3",
    "pytesseract",
    "pdf2image",
    "PIL",
    "pandas",
    "numpy",
    "spacy",
    "cv2",        # comes from opencv-python
    "PyPDF2",
    "pytest"
]

print("🔍 Checking Python libraries...\n")
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"✅ {pkg} is installed")
    except ImportError:
        print(f"❌ {pkg} is missing")

print("\n🔍 Checking external dependencies...\n")
try:
    out = subprocess.check_output(["tesseract", "--version"]).decode().splitlines()[0]
    print(f"✅ Tesseract binary found: {out}")
except Exception as e:
    print(f"❌ Tesseract not found: {e}")

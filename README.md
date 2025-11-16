# **AI-Powered Intelligent Document Processing Pipeline for Historical NOAA Storm Data**


## **1. Overview**

Across the United States, the National Oceanic and Atmospheric Administration (NOAA) has published monthly *Storm Data* records for decades.
While recent datasets are digital and structured, **millions of older reports exist only as handwritten, scanned, or low-resolution PDF documents** (some dating back to the 1950s).

These documents contain valuable information:

* Storm location
* Date & time
* Path length & width
* Fatalities & injuries
* Property and crop damage
* storm descriptions

However, the **handwritten tables, faded ink, and inconsistent formatting** make them extremely difficult to retrieve manually — and almost impossible to use for large-scale research or analysis.

### **This project solves that problem.**

This repository implements a **fully automated, AI-powered document processing pipeline** that:

1. **Ingests raw historical NOAA PDFs**
2. **Automatically splits multi-page files**
3. **Uses OCR to detect which pages actually contain storm tables**
4. **Extracts structured data using Gemini (LLM-based extraction)**
5. **Cleans & normalizes results**
6. **Exports final structured data to Google Sheets for analysis/visualization**

This transforms inaccessible historical storm records into **clean, queryable, machine-readable datasets** — ready for climate research, vulnerability analysis, emergency management, insurance modeling, and academic study.

**This pipeline uses REAL NOAA documents,**
It demonstrates the ability to handle **real-world noise**, handwriting, scanned text, and degraded PDFs.


## **2. Key Features**

* **Automated PDF ingestion**
  Place any number of NOAA PDF reports in `data/input/` and run the pipeline.

* **Automatic page splitting**
  Each PDF is converted into individual page-level PDFs.

* **Intelligent page scoring**
  OCR determines whether a page contains meaningful storm table content.

* **High-accuracy OCR (printed + handwritten)**
  Custom preprocessing improves the recognition of old scanned handwriting.

* **LLM-based structured extraction**
  Using **Gemini** (Flash / Flash-Lite) to extract fields into consistent JSON.

* **Continuation handling**
  Pages for the same month are combined in order into a single JSON.

* **Google Sheets export**
  Final cleaned rows are appended to a central live Sheet for visualization.

* **Modular & configurable**
  Each stage can be enabled/disabled via `.env` flags.

* **Extensible for future work**
  Architecture supports adding a queryable database or dashboards.
  Automating the process of getting the PDF to feed as input.
  Enhancing the pipeline using better models and cleaning the data more accurately


## **3. System Architecture**

```
/data/input
    ↓ PDF ingestion
PDF Splitter
    ↓ Single-page PDFs
Page OCR + Scoring
    ↓ Keep or discard
/data/raw/<month_year>/
    ↓ OCR preprocessing
Gemini LLM Extraction
    ↓ JSON output
/data/processed/<month_year>.json
    ↓ Cleaning + normalization
Google Sheets Exporter
    ↓ Live analytics-ready sheet
```


## **4. Repository Structure**

```
AIDP_StormData/
│
├── data/
│   ├── input/                # Drop raw NOAA PDFs here
│   ├── raw/                  # Kept pages after OCR scoring
│   ├── error/                # Discarded noisy pages
│   ├── processed/            # JSON extracted via Gemini
│   ├── archived_input/       # Original PDFs after processing
│   ├── archived_raw/         # Raw page folders after extraction
│   └── archived_processed/   # JSON files after Google Sheets export
│
├── logs/
│   └── ocr_text/             # Optional OCR debug text (controlled by flag)
│
├── src/
│   ├── ingestion/            # PDF splitter
│   ├── pipeline/             # Main pipeline runner
│   ├── extraction/           # Gemini extractor
│   ├── export/               # Google Sheets exporter
│   └── utils/                # Logger + configuration
│
├── credentials/              # Google service account JSON (gitignored)
├── .env                      # Environment configuration (gitignored)
└── requirements.txt
└── main.py                   # Single entrypoint for full pipeline
```


## **5. Prerequisites**

### **Python Version**

`Python 3.10+`

### **Python Libraries**

Install via:

```bash
pip install -r requirements.txt
```

### **You must create a `.env` file**

(Already ignored by git.)

Example:

```env
# Gemini
GEMINI_API_KEY=your_api_key_here
ENABLE_GEMINI=true #set to false skip gemini extractor run

# Google Sheets
ENABLE_SHEETS_EXPORT=true # set to false to skip exporting
GOOGLE_SHEET_ID=your_sheet_id_here 
GOOGLE_SHEETS_ENABLED=true
SERVICE_ACCOUNT_FILE=credentials/service_account.json

# OCR Debug
SAVE_OCR_DEBUG_TEXT=true #set to false to skip saving ocr.txt files

# Local paths (optional)
LOCAL_INPUT_PATH=data/input
LOCAL_RAW_PATH=data/raw
LOCAL_PROCESSED_PATH=data/processed
LOCAL_ERROR_PATH=data/error
LOG_PATH=logs

```


## **6. Environment Flags — How the Pipeline Controls Work**

You can **run the entire end-to-end pipeline** or **skip any section** simply by toggling flags.

### **Enable/Disable Gemini Extraction**

```env
ENABLE_GEMINI=true   # run extraction
ENABLE_GEMINI=false  # skip LLM extraction
```

### **Enable/Disable Google Sheets Export**

```env
ENABLE_SHEETS_EXPORT=true
ENABLE_SHEETS_EXPORT=false
```

### **Enable/Disable OCR Debug Text Saving**

OCR text files fill up space — keep them only when debugging.

```env
SAVE_OCR_DEBUG_TEXT=true
SAVE_OCR_DEBUG_TEXT=false
```

These flags allow:

* Faster debugging
* Running individual stages
* Saving API quota
* Reprocessing only parts you need


## **7. How to Run the Pipeline**

### **Option 1 — Full End-to-End Pipeline**

```bash
python main.py
```

### **Option 2 — OCR Only**

```bash
ENABLE_GEMINI=false ENABLE_SHEETS_EXPORT=false python main.py
```

### **Option 3 — Only Gemini Extraction**

```bash
python -m src.extraction.gemini_extractor
```

### **Option 4 — Only Google Sheets Export**

```bash
python -m src.export.google_sheets_exporter
```


## **8. What Happens at Each Stage**

### **1. PDF Ingestion**

Put your raw NOAA PDFs into: Format <mon_yyyy.pdf> ex: Jan_1993.pdf

```
data/input/
```

### **2. PDF Splitting**

Each multi-page PDF becomes individual page files, that way it is easy to feed to the LLM in the next steps.

### **3. OCR + Page Scoring**

Each page is scanned for NOAA header keywords:

* location
* date
* path
* injured
* damage
* character of storm
* …etc

Only pages with real storm tables are kept.

### **4. Gemini Extraction**

All pages for a month (e.g., `jan_1993`) are:

* Sorted in correct order for page continuation
* Sent to Gemini for structured JSON extraction
* Combined into one JSON file for one input PDF

### **5. Google Sheets Export**

Final cleaned rows are appended to a sheet with all years combined:

```
month | year | state | location | date | path_length | ... | description
```


## **9. Real-World Challenges & Solutions**

| Challenge                       | Solution                                      |
| ------------------------------- | --------------------------------------------- |
| Handwritten and degraded text   | Custom grayscale + sharpening preprocessing   |
| Noisy scanned pages             | Keyword-based page scoring (THRESHOLD=6)      |
| Inconsistent table structure    | LLM-driven extraction + normalization         |
| Continuation pages              | Folder-level merging with page order tracking |
| API quota limits                | Rate-limiting & retry logic                   |
| Mixed formatting across decades | Standardized JSON schema                      |

This demonstrates your ability to solve real data engineering + AI problems — not synthetic Kaggle tasks.


## **10. Extending or Reusing This Pipeline**

Any developer or researcher can adapt this pipeline for:

* Processing other government archives
* Insurance claim digitization
* Old newspaper or weather bulletin extraction
* Geological or hydrology historical reports
* Large-scale document OCR + LLM extraction workflows
* General ETL pipelines that combine OCR + LLM

The pipeline is **completely modular**, so you can replace:

* Gemini → OpenAI / Claude / Local LLM
* Google Sheets → BigQuery / DynamoDB / Postgres
* OCR engine → Tesseract + PaddleOCR / AWS Textract


## **11. Future Enhancements**

* Direct export to Google BigQuery or any other DB for querying
* Interactive dashboard
* Automated scheduling via Airflow
* Automated extraction of PDF files to the input folder
* Multi-disaster support (floods, wildfires, earthquakes)
* Fine-tuned OCR models for historical handwriting
* Enhancing data cleaning and using better models for data extraction


## **12. Author & Academic Credit**

**Developed by:**
**Nagamedha Sakhamuri**
Graduate Student – Georgia State University

**Capstone Project Advisor:**
**Dr. Chetan Tiwari**
Department of Geosciences & Computer Science
Georgia State University


## **13. License**

@GSU 


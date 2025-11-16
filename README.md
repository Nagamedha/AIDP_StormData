# **AI-Powered Intelligent Document Processing Pipeline for Historical NOAA Storm Data**

### 1. Overview

Across the United States, the National Oceanic and Atmospheric Administration (NOAA) has published monthly *Storm Data* records for decades. While recent datasets are digital and structured, **millions of older reports exist only as handwritten, scanned, or low-quality PDF documents**, many dating back to the 1950s.

These documents contain critical information such as:

* Storm location
* Date & time
* Path length & width
* Fatalities & injuries
* Property & crop damage
* Character of storm

However, the **inconsistent formatting, handwritten tables, faded ink, and scanning artifacts** make them extremely difficult to extract manually — and nearly impossible to use at scale.

#### **This project solves that problem.**

This repository implements a **fully automated, AI-powered document processing pipeline** that:

1. Ingests raw historical NOAA PDFs
2. Splits multi-page documents
3. Performs OCR and detects pages with storm tables
4. Uses Google Gemini to extract structured JSON
5. Cleans, formats, and validates all fields
6. Exports the final dataset to Google Sheets for analysis

This transforms inaccessible historical storm records into **clean, machine-readable datasets** suitable for:

* Climate and meteorology research
* Vulnerability & risk assessments
* Insurance and actuarial modeling
* Emergency management
* Academic projects & historical analyses

The pipeline operates on **real NOAA storm documents**, not synthetic datasets—demonstrating robust handling of messy, inconsistent, real-world data.

---

### 2. Key Features

* **Automated PDF ingestion**
  Drop any NOAA PDF into `data/input/`.

* **Automatic page splitting**
  Ensures clean page-level processing.

* **Keyword-based intelligent page scoring**
  Keeps only pages containing storm tables.

* **Enhanced OCR preprocessing**
  Sharpens old handwriting and faint printed text.

* **LLM-based structured extraction (Gemini)**
  Interprets handwritten tables and produces normalized JSON.

* **Continuation-page handling**
  Pages are merged in correct order before extraction.

* **Google Sheets export**
  Data becomes instantly available for dashboards.

* **Flag-based modular execution**
  Enable/disable OCR debug, Gemini, Sheets export, etc.

* **Extensible design**
  Easy to integrate with BigQuery, DynamoDB, or any OCR/LLM engine.

---

### 3. System Architecture

```
PHASE 1 — INPUT
[ Raw NOAA PDFs ] → [ PDF Splitter ] → [ Single-Page PDFs ]

PHASE 2 — PAGE FILTERING
[ OCR + Keyword Scoring ] → Keep → data/raw/<mm_yyyy>/
                           → Discard → data/error/<mm_yyyy>/

PHASE 3 — EXTRACTION
data/raw/<mm_yyyy>/ → [ OCR Preprocessing ] → [ Gemini LLM Extraction ]
                    → [ Structured JSON ] → data/processed/<mm_yyyy>.json

PHASE 4 — CLEANING
[ Field Cleaning ] → [ Numeric / Date Normalization ] → [ Final JSON ]

PHASE 5 — EXPORT & ANALYTICS
[ Google Sheets Exporter ] → [ Live Analytics Sheet ]                         
```

---

### 4. Repository Structure

```
AIDP_StormData/
│
├── data/
│   ├── input/                # Raw NOAA PDFs
│   ├── raw/                  # Kept pages after OCR scoring
│   ├── error/                # Discarded pages
│   ├── processed/            # Gemini-extracted JSON
│   ├── archived_input/       # Original PDFs after ingest
│   ├── archived_raw/         # Raw folders after extraction
│   ├── archived_processed/   # JSON after Sheets export
│   ├── logs/                 # log for tracking workflow
│
├── logs/
│   └── ocr_text/             # OCR debug text (optional)
│
├── src/
│   ├── ingestion/            # page_splitter.py
│   ├── pipeline/             # pipeline_runner.py
│   ├── extraction/           # gemini_extractor.py
│   ├── export/               # google_sheets_exporter.py
│   └── utils/                # config, handlers, logger
│
├── credentials/              # Google service account (ignored)
├── .env                      # Environment variables (ignored)
├── check_deps.py             # Dependency checker
├── main.py                   # Main pipeline entry
└── requirements.txt
```

---

### 5. Prerequisites

### **Python Version**

```
Python 3.10+
```

### **Install dependencies**

```
pip install -r requirements.txt
```

### **Create a `.env` file**

*(Must NOT be committed to GitHub)*

```env
# Gemini
GEMINI_API_KEY=your_key_here
ENABLE_GEMINI=true #set to false to skip Gemini extractor run

# Google Sheets Export
ENABLE_SHEETS_EXPORT=true #set to false to skip exporting to Google Sheet
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEET_ID=your_sheet_id_here
SERVICE_ACCOUNT_FILE=credentials/service_account.json # This service account should have edit access to the Google Sheet

# OCR Debug
SAVE_OCR_DEBUG_TEXT=true #set to false to skip saving ocr.txt files

# Paths
LOCAL_INPUT_PATH=data/input
LOCAL_RAW_PATH=data/raw
LOCAL_PROCESSED_PATH=data/processed
LOCAL_ERROR_PATH=data/error
LOG_PATH=logs
```

---

### 6. How to Fork & Run Locally

### **Step 1 — Fork**

On GitHub → **Fork → Create Fork**

### **Step 2 — Clone**

```
git clone https://github.com/<your-username>/AIDP_StormData.git
cd AIDP_StormData
```

### **Step 3 — Create & Activate Virtual Environment**

```
python3 -m venv venv
source venv/bin/activate
```

### **Step 4 — Install Requirements**

```
pip install -r requirements.txt
```

### **Step 5 — Add .env**

Copy the template above.

### **Step 6 — Add Google Credentials**

```
credentials/service_account.json
```

### **Step 7 — Add NOAA PDFs**

```
data/input/Jan_1993.pdf
data/input/Oct_1970.pdf
```

### **Step 8 — Run**

**Full Pipeline:**
```
python main.py
```

**OCR Only:**
```
ENABLE_GEMINI=false ENABLE_SHEETS_EXPORT=false python main.py
```

**Gemini Extraction Only:**
```
python -m src.extraction.gemini_extractor
```

**Google Sheets Export Only:**
```
python -m src.export.google_sheets_exporter
```

---

### 7. What Happens at Each Stage

1. **PDF Ingestion** → Move raw NOAA PDFs into `data/input/`
2. **Splitting** → Each PDF becomes page-level PDFs
3. **OCR + Scoring** → Pages with storm tables are detected
4. **Gemini Extraction** → Ordered pages → combined → JSON
5. **Google Sheets Export** → Data appended for visualization

---

### 8. Real-World Challenges & How We Solved Them

### **Challenges Table**

| Challenge                              | Description                                           | Solution                                                        |
| -------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| **Handwritten & degraded text**        | Pages from 1950–1970 were faint, skewed, or scribbled | Added grayscale → sharpening → threshold OCR preprocessing      |
| **Noise, smudges, footers, artifacts** | OCR picked up page numbers, smears, ink blotches      | Implemented keyword scoring (THRESHOLD=6) to filter bad pages   |
| **Continuation across pages**          | Gemini sometimes treated page 2 as a new event table  | Combined pages *in order* into a single extraction prompt       |
| **OCR structural inconsistency**       | Column boundaries differed widely across decades      | Used LLM-based flexible interpretation instead of rigid parsing |
| **Gemini API rate limits**             | Experienced 503 errors & daily quota issues           | Added backoff, retry logic, selectable Flash/Flash-Lite models  |
| **Google Sheets numeric formatting**   | Numbers appeared with `'` prefix (treated as strings) | Cleaned & normalized all numeric fields before export           |

---

### 9. Extending or Reusing This Pipeline

This system can be adapted for:

* Government or archival digitization projects
* Insurance claims digitization
* Extracting historical newspapers/weather bulletins
* Geological or hydrology reports
* Enterprise OCR + LLM ETL workflows
* Automated data extraction for research datasets

Modular components allow swapping:

* **Gemini → OpenAI / Claude / Local LLMs**
* **Google Sheets → BigQuery / DynamoDB / PostgreSQL**
* **Tesseract → PaddleOCR / AWS Textract / Azure OCR**

---

### 10. Future Enhancements

* Integrate with a proper analytical database
* Interactive dashboard
* Automated monthly NOAA ingestion
* Fine-tuned OCR models for handwriting
* Add multi-disaster support (floods, wildfires, earthquakes)
* Improve numeric value normalization
* Build historical trend-detection tools

---

### 11. Author & Academic Credit

**Developed By:** <br>
 &nbsp;&nbsp;&nbsp;&nbsp; **Nagamedha Sakhamuri** <br>
 &nbsp;&nbsp;&nbsp;&nbsp; Graduate Student <br>
 &nbsp;&nbsp;&nbsp;&nbsp; Georgia State University

**Capstone Advisor:** <br>
 &nbsp;&nbsp;&nbsp;&nbsp; **Dr. Chetan Tiwari** <br>
 &nbsp;&nbsp;&nbsp;&nbsp; Department of Geosciences & Computer Science <br>
 &nbsp;&nbsp;&nbsp;&nbsp; Georgia State University

---

### 12. License

© Georgia State University

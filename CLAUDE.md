# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **computer vision research project** focused on extracting quantitative biomarkers from brain MRI scans to study Alzheimer's disease and neurodegenerative disorders. The pipeline uses **ANTsPyNet HippMapp3r** (state-of-the-art deep learning) to perform hippocampus segmentation and volume analysis.

**Dataset**: OASIS-2 longitudinal brain MRI dataset (209 scans from 82 patients)

**Key Goal**: Move beyond classification to provide measurable indicators (hippocampal volume, atrophy patterns) that correlate with dementia progression.

## Directory Structure

```
cv/
├── raw data/
│   ├── Oasis-2/
│   │   └── part1_extracted/OAS2_RAW_PART1/    # MRI scans (NIfTI format)
│   │       └── OAS2_####_MR#/RAW/*.nifti.img/hdr
│   └── objective.txt                           # Project goals (future Streamlit app)
├── results/
│   ├── skull_stripped/                         # Preprocessed brain images (*.nii.gz)
│   ├── hippocampus_segmentation/               # Segmented hippocampus masks (*.nii.gz)
│   ├── volumes/                                # CSV files with volume measurements
│   │   ├── hippocampus_volumes_all.csv        # All scan volumes
│   │   ├── longitudinal_changes.csv           # Patient volume changes over time
│   │   └── volumes_with_demographics.csv      # Merged with clinical data
│   └── visualizations/                         # 2D/3D visualizations (*.png, *.html)
├── final.ipynb                                 # Main analysis notebook
├── final.html                                  # Exported notebook for sharing
├── visual.py                                   # Interactive visualization script
├── project_architecture.svg                    # System architecture diagram
├── OASIS_demographic.xlsx                      # Patient demographics & CDR scores
├── README.md                                   # Detailed project documentation
└── venv/                                       # Python virtual environment
```

## Technology Stack

- **ANTs/ANTsPy**: Medical image processing and registration
- **ANTsPyNet**: Deep learning models for brain segmentation (HippMapp3r)
- **Nibabel**: NIfTI medical image I/O
- **NumPy/Pandas**: Data processing and analysis
- **Matplotlib/Plotly**: 2D and interactive 3D visualizations
- **scikit-image**: Marching cubes for 3D surface extraction
- **scipy**: Statistical analysis (t-tests, ANOVA, correlations)

## Development Setup

### Virtual Environment
The project uses a Python virtual environment located in `venv/`. Activate it:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Install Dependencies
```bash
pip install antspyx antspynet nibabel matplotlib plotly scikit-image pandas numpy scipy openpyxl
```

### Running the Analysis

**Main Notebook**: `final.ipynb`
- Open in Jupyter Notebook: `jupyter notebook final.ipynb`
- Or use VS Code with Jupyter extension
- Run cells sequentially (Shift+Enter)
- Processing all 209 scans takes ~3-4 hours
- Exports results to `final.html` for sharing

**Interactive Visualizer**: `visual.py`
- Command-line menu interface: `python visual.py`
- Provides interactive scan selection by patient ID, volume, or scan number
- Shows 2D slices (axial/coronal/sagittal) and 3D hippocampus rendering
- Requires results from `final.ipynb` first (reads CSV files from `results/volumes/`)
- 3D visualizations saved as HTML files in `results/visualizations/`

## Pipeline Architecture

The analysis pipeline (`final.ipynb`) implements a 5-stage workflow:

### 1. Scan Discovery
```python
# Recursively finds all MRI scans in nested OASIS-2 directory
scans_df = find_all_scans(DATA_DIR)
# Returns DataFrame: patient_id, session, scan_name, img_path
```
**Output**: Inventory of 209 scans from 82 patients

### 2. Skull Stripping (Preprocessing)
```python
brain_extraction = antspynet.brain_extraction(img, modality="t1")
brain = img * brain_extraction['brain_mask']
```
- Uses deep learning model to remove skull, scalp, non-brain tissues
- Generates binary mask: 1=brain, 0=background
- **Time**: ~30-60 seconds per scan
- **Output**: Saved to `results/skull_stripped/{scan_name}_brain.nii.gz`

### 3. Hippocampus Segmentation
```python
hippo_seg = antspynet.hippmapp3r_segmentation(brain)
# Output: 0=background, 1=left hippocampus, 2=right hippocampus
```
- **Model**: HippMapp3r CNN trained on expert-annotated MRI scans
- **Time**: ~1-2 minutes per scan
- **Expected volumes**: 6-10 cm³ total (healthy adults), 4-6 cm³ (dementia patients)
- **Output**: Saved to `results/hippocampus_segmentation/{scan_name}_hippo.nii.gz`

### 4. Volume Calculation
```python
voxel_vol_cm3 = np.prod(brain.spacing) / 1000  # mm³ to cm³
left_vol = np.sum(hippo_data == 1) * voxel_vol_cm3
right_vol = np.sum(hippo_data == 2) * voxel_vol_cm3
total_vol = left_vol + right_vol
```
- Counts voxels labeled as hippocampus
- Converts to cm³ using voxel spacing from MRI header
- **Output**: `results/volumes/hippocampus_volumes_all.csv`

### 5. Longitudinal & Statistical Analysis
- Merges with demographics (`OASIS_demographic.xlsx`)
- Calculates temporal changes for patients with multiple sessions
- Performs statistical tests (t-tests, ANOVA, correlations)
- Generates summary plots and clinical validation figures
- **Outputs**:
  - `longitudinal_changes.csv`
  - `volumes_with_demographics.csv`
  - `summary.png`, `clinical_validation.png`

## Data Files

### Input
- **MRI scans**: `.nifti.img` + `.nifti.hdr` pairs (Analyze 7.5 format)
- **Demographics**: `OASIS_demographic.xlsx`
  - Contains: CDR (Clinical Dementia Rating), MMSE scores, age, diagnosis

### Output
- **hippocampus_volumes_all.csv**: All measurements
  - Columns: scan_name, patient_id, session, status, left_cm3, right_cm3, total_cm3
- **longitudinal_changes.csv**: Temporal changes
  - Columns: patient_id, n_sessions, first_volume_cm3, last_volume_cm3, change_cm3, change_pct
- **volumes_with_demographics.csv**: Merged with clinical data
  - Adds: CDR, MMSE, Group (Demented/Nondemented/Converted), Age

## Statistical Analysis & Clinical Validation

The pipeline performs comprehensive statistical tests to validate biomarker significance:

### 1. Group Comparisons
**Demented vs Nondemented**
- Independent t-test on hippocampal volumes
- Effect size (Cohen's d): measures clinical significance
- Typical result: p < 0.001 (highly significant)

### 2. Dementia Severity (CDR)
**Clinical Dementia Rating correlation**
- Spearman correlation (ordinal data)
- One-way ANOVA across CDR groups (0, 0.5, 1.0, 2.0)
- Tests if volume decreases with increasing dementia severity

### 3. Cognitive Function (MMSE)
**Mini-Mental State Examination correlation**
- Pearson correlation (continuous variables)
- Higher MMSE scores → larger hippocampal volumes
- Quantifies relationship between brain structure and cognition

### 4. Longitudinal Changes
**Volume changes over time**
- Percent change calculations for patients with multiple sessions
- Rate of atrophy (cm³ per session interval)
- Identifies patients with accelerated neurodegeneration

**Key Finding**: Hippocampal volume is highly correlated with dementia progression (p < 0.001), validating it as an objective biomarker for Alzheimer's disease.

## Visualization

### 2D Slice Views
**Three orthogonal planes:**
- **Axial**: Horizontal slices (top-down view)
- **Coronal**: Front-to-back slices (face-on view)
- **Sagittal**: Side slices (profile view)

**Display method:**
- Brain tissue in grayscale
- Hippocampus overlay in red (semi-transparent)
- Algorithm automatically finds slices with maximum hippocampus visibility

### 3D Interactive Renderings
**Surface extraction using marching cubes:**
- Brain surface: transparent light blue (70th percentile threshold, step_size=3)
- Hippocampus: solid red (full resolution, step_size=1)

**Output format:**
- Interactive Plotly HTML files (self-contained, no server required)
- Rotation, zoom, pan controls built-in
- Saved to `results/visualizations/3D_{scan_name}.html`

### Summary Plots
**Generated in notebook:**
- `summary.png`: 6-panel figure showing volume distributions and longitudinal changes
- `clinical_validation.png`: 6-panel figure with statistical tests (t-tests, correlations, ANOVA)
- `roc_auc_analysis.png`: ROC curve for classification performance (if applicable)

## Important Notes

### Data Format
- **OASIS-2 naming**: `OAS2_{patient_id}_MR{session}`
  - Example: `OAS2_0001_MR1` = Patient 0001, Session 1
- **Patient IDs**: 4-digit zero-padded integers (0001-0099)
- When merging with demographics, ensure patient_id is properly formatted

### Common Issues

1. **ITK Errors**: "Requested region outside largest possible region"
   - Caused by incompatible MRI dimensions or corrupted files
   - ~33 out of 209 scans failed with this error
   - No known fix; skip these scans

2. **Low Volumes**: Segmentations < 6 cm³ may indicate under-segmentation
   - Verify by visual inspection
   - Could be actual atrophy or model error

3. **TensorFlow Warnings**: Retracing warnings are normal
   - Appears during first few HippMapp3r calls
   - Does not affect results

### Performance
- **Single scan**: ~2-3 minutes (skull stripping + segmentation)
- **Full dataset (209 scans)**: 3-4 hours
- Pipeline saves progress every 50 scans (`progress.csv`)
- Memory usage: ~4-6 GB RAM during processing
- GPU acceleration: Optional (TensorFlow/CUDA compatible)

## File Paths

All paths in the code use Windows-style absolute paths starting with:
```python
BASE_DIR = Path(r"C:\Users\Ratul\Desktop\cv")
```

When modifying code, update `BASE_DIR` if the project is moved.

## Code Organization

### Main Components
- **`final.ipynb`**: Complete analysis pipeline from raw MRI to statistical validation
  - Notebook is self-contained with markdown explanations
  - Exports to `final.html` for sharing without running code

- **`visual.py`**: Standalone visualization tool with 4 key functions:
  - `visualize_hippocampus(scan_name)`: Creates 2D slices and 3D rendering for single scan
  - `display_menu()`: Main interactive menu loop
  - `browse_scans()`: Paginated scan browsing interface
  - `search_by_patient()`: Patient-specific scan lookup

### Data Flow
```
Raw MRI (.nifti.img/hdr)
  ↓ [antspynet.brain_extraction]
Skull-stripped brain (.nii.gz)
  ↓ [antspynet.hippmapp3r_segmentation]
Hippocampus segmentation mask (.nii.gz)
  ↓ [Volume calculation]
CSV files with measurements
  ↓ [Merge with demographics]
Statistical analysis & plots
  ↓ [visual.py]
Interactive 3D visualizations
```

## Future Directions

From `objective.txt`:
- Deploy as **Streamlit app** for interactive web-based exploration
- Allow users to upload their own MRI scans for analysis
- Build predictive model: volume → dementia stage classification
- Expand to multi-region analysis (cortical thickness, ventricular volume, amygdala)

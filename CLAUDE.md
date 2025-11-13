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
│   └── objective.txt                           # Project goals
├── results/
│   ├── skull_stripped/                         # Preprocessed brain images
│   ├── hippocampus_segmentation/               # Segmented hippocampus masks
│   ├── volumes/                                # CSV files with volume measurements
│   │   ├── hippocampus_volumes_all.csv        # All scan volumes
│   │   ├── longitudinal_changes.csv           # Patient volume changes over time
│   │   └── volumes_with_demographics.csv      # Merged with clinical data
│   └── visualizations/                         # 2D/3D visualizations
├── final.ipynb                                 # Main analysis notebook
├── visual.py                                   # Interactive visualization script
├── OASIS_demographic.xlsx                      # Patient demographics & CDR scores
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
- Open in Jupyter or VS Code
- Run cells sequentially
- Processing all 209 scans takes ~3-4 hours

**Interactive Visualizer**: `visual.py`
- Provides dropdown interface to view any scan
- Shows 2D slices and 3D hippocampus rendering
- Requires results from `final.ipynb` first

## Key Pipeline Steps

### 1. Scan Discovery
```python
# Finds all MRI scans in nested directory structure
scans_df = find_all_scans(DATA_DIR)
# Returns: patient_id, session, scan_name, img_path
```

### 2. Skull Stripping
```python
brain_extraction = antspynet.brain_extraction(img, modality="t1")
brain = img * brain_extraction['brain_mask']
```
- Removes skull and non-brain tissue
- Takes ~30-60 seconds per scan

### 3. Hippocampus Segmentation
```python
hippo_seg = antspynet.hippmapp3r_segmentation(brain)
# Output values: 0=background, 1=left hippocampus, 2=right hippocampus
```
- Uses deep learning model (HippMapp3r)
- Takes ~1-2 minutes per scan
- Expected total volume: 6-10 cm³ (healthy adults)

### 4. Volume Calculation
```python
voxel_vol_cm3 = np.prod(brain.spacing) / 1000  # mm³ to cm³
left_vol = np.sum(hippo_data == 1) * voxel_vol_cm3
right_vol = np.sum(hippo_data == 2) * voxel_vol_cm3
```

### 5. Longitudinal Analysis
- Tracks volume changes across multiple sessions per patient
- Calculates rate of change (cm³ per session interval)
- Identifies patients with significant atrophy

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

## Clinical Validation

The analysis performs statistical tests to validate biomarker significance:

1. **Demented vs Nondemented Comparison**
   - Independent t-test on hippocampal volumes
   - Effect size (Cohen's d)

2. **CDR Correlation**
   - Spearman correlation with dementia severity
   - One-way ANOVA across CDR groups (0, 0.5, 1.0, 2.0)

3. **MMSE Correlation**
   - Pearson correlation with cognitive function
   - Higher MMSE = larger hippocampal volume

**Key Finding**: Hippocampal volume is highly correlated with dementia progression (p < 0.001)

## Visualization

### 2D Slices
- Axial, coronal, sagittal views
- Brain in grayscale + hippocampus overlay in red
- Automatically finds slices with maximum hippocampus visibility

### 3D Renderings
- Brain surface (transparent blue)
- Hippocampus (solid red)
- Interactive Plotly visualizations saved as HTML
- Marching cubes algorithm for surface extraction

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
- Save progress every 50 scans (`progress.csv`)

## File Paths

All paths in the code use Windows-style absolute paths starting with:
```python
BASE_DIR = Path(r"C:\Users\Ratul\Desktop\cv")
```

When modifying code, update `BASE_DIR` if the project is moved.

## Future Directions

From `objective.txt`:
- Deploy as **Streamlit app** for interactive exploration
- Allow users to upload their own MRI scans
- Predict dementia stage from volume measurements
- Add cortical thickness and ventricular volume analysis

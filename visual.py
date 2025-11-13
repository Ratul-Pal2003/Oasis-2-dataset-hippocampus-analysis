# ============================================
# SIMPLE INTERACTIVE HIPPOCAMPUS VIEWER
# Select any scan from dropdown to visualize
# ============================================

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from skimage import measure
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown
import warnings
warnings.filterwarnings('ignore')

# ============================================
# SETUP
# ============================================

BASE_DIR = Path(r"C:\Users\Ratul\Desktop\cv")
RESULTS_DIR = BASE_DIR / "results"
SKULL_STRIPPED_DIR = RESULTS_DIR / "skull_stripped"
HIPPOCAMPUS_DIR = RESULTS_DIR / "hippocampus_segmentation"
VIZ_DIR = RESULTS_DIR / "visualizations"

# Load results
results_df = pd.read_csv(RESULTS_DIR / "volumes" / "hippocampus_volumes_all.csv")
success_df = results_df[results_df['status'] == 'success'].copy()

print("=" * 80)
print("🔍 INTERACTIVE HIPPOCAMPUS VIEWER")
print("=" * 80)
print(f"\nTotal available scans: {len(success_df)}")
print(f"Volume range: {success_df['total_cm3'].min():.2f} - {success_df['total_cm3'].max():.2f} cm³")

# ============================================
# VISUALIZATION FUNCTION
# ============================================

def visualize_hippocampus(scan_name):
    """
    Visualize a single scan with 2D slices and 3D view
    """
    
    # Get files
    brain_file = SKULL_STRIPPED_DIR / f"{scan_name}_brain.nii.gz"
    hippo_file = HIPPOCAMPUS_DIR / f"{scan_name}_hippo.nii.gz"
    
    if not brain_file.exists() or not hippo_file.exists():
        print(f"❌ Files not found for {scan_name}")
        return
    
    # Load data
    print(f"\n📂 Loading {scan_name}...")
    brain_data = nib.load(brain_file).get_fdata()
    hippo_data = nib.load(hippo_file).get_fdata()
    hippo_mask = hippo_data > 0
    
    # Get volume info
    vol_info = success_df[success_df['scan_name'] == scan_name].iloc[0]
    
    print(f"📊 Volumes:")
    print(f"   Total: {vol_info['total_cm3']:.2f} cm³")
    print(f"   Left:  {vol_info['left_cm3']:.2f} cm³")
    print(f"   Right: {vol_info['right_cm3']:.2f} cm³")
    
    # Find best slices
    axial_sums = [np.sum(hippo_mask[:, :, z]) for z in range(hippo_data.shape[2])]
    best_axial = np.argmax(axial_sums) if max(axial_sums) > 0 else hippo_data.shape[2] // 2
    
    coronal_sums = [np.sum(hippo_mask[:, y, :]) for y in range(hippo_data.shape[1])]
    best_coronal = np.argmax(coronal_sums) if max(coronal_sums) > 0 else hippo_data.shape[1] // 3
    
    sagittal_sums = [np.sum(hippo_mask[x, :, :]) for x in range(hippo_data.shape[0])]
    best_sagittal = np.argmax(sagittal_sums) if max(sagittal_sums) > 0 else hippo_data.shape[0] // 2
    
    # ============================================
    # 2D VISUALIZATION
    # ============================================
    
    print("🎨 Creating 2D views...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Row 1: Brain only
    axes[0, 0].imshow(brain_data[:, :, best_axial].T, cmap='gray', origin='lower')
    axes[0, 0].set_title(f'Brain - Axial (slice {best_axial})', fontsize=12)
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(brain_data[:, best_coronal, :].T, cmap='gray', origin='lower')
    axes[0, 1].set_title(f'Brain - Coronal (slice {best_coronal})', fontsize=12)
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(brain_data[best_sagittal, :, :].T, cmap='gray', origin='lower')
    axes[0, 2].set_title(f'Brain - Sagittal (slice {best_sagittal})', fontsize=12)
    axes[0, 2].axis('off')
    
    # Row 2: Hippocampus overlay
    axes[1, 0].imshow(brain_data[:, :, best_axial].T, cmap='gray', origin='lower', alpha=0.7)
    axes[1, 0].imshow(hippo_mask[:, :, best_axial].T, cmap='Reds', origin='lower', alpha=0.7)
    axes[1, 0].set_title('Hippocampus - Axial', fontsize=12)
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(brain_data[:, best_coronal, :].T, cmap='gray', origin='lower', alpha=0.7)
    axes[1, 1].imshow(hippo_mask[:, best_coronal, :].T, cmap='Reds', origin='lower', alpha=0.7)
    axes[1, 1].set_title('Hippocampus - Coronal', fontsize=12)
    axes[1, 1].axis('off')
    
    axes[1, 2].imshow(brain_data[best_sagittal, :, :].T, cmap='gray', origin='lower', alpha=0.7)
    axes[1, 2].imshow(hippo_mask[best_sagittal, :, :].T, cmap='Reds', origin='lower', alpha=0.7)
    axes[1, 2].set_title('Hippocampus - Sagittal', fontsize=12)
    axes[1, 2].axis('off')
    
    title = f'{scan_name}\nTotal: {vol_info["total_cm3"]:.2f} cm³ | Left: {vol_info["left_cm3"]:.2f} cm³ | Right: {vol_info["right_cm3"]:.2f} cm³'
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    # ============================================
    # 3D VISUALIZATION
    # ============================================
    
    print("🎨 Creating 3D view...")
    
    try:
        # Brain surface
        brain_thresh = np.percentile(brain_data[brain_data > 0], 70)
        brain_verts, brain_faces, _, _ = measure.marching_cubes(
            brain_data, level=brain_thresh, step_size=3
        )
        
        # Hippocampus surface
        hippo_verts, hippo_faces, _, _ = measure.marching_cubes(
            hippo_data, level=0.5, step_size=1
        )
        
        print(f"   Brain: {len(brain_verts):,} vertices")
        print(f"   Hippocampus: {len(hippo_verts):,} vertices")
        
        # Create figure
        fig = go.Figure()
        
        # Brain (transparent blue)
        fig.add_trace(go.Mesh3d(
            x=brain_verts[:, 0], y=brain_verts[:, 1], z=brain_verts[:, 2],
            i=brain_faces[:, 0], j=brain_faces[:, 1], k=brain_faces[:, 2],
            color='lightblue', opacity=0.15, name='Brain',
            lighting=dict(ambient=0.5, diffuse=0.6),
            showlegend=True
        ))
        
        # Hippocampus (solid red)
        fig.add_trace(go.Mesh3d(
            x=hippo_verts[:, 0], y=hippo_verts[:, 1], z=hippo_verts[:, 2],
            i=hippo_faces[:, 0], j=hippo_faces[:, 1], k=hippo_faces[:, 2],
            color='red', opacity=0.95, name='Hippocampus',
            lighting=dict(ambient=0.3, diffuse=0.8, specular=1.0, roughness=0.1),
            showlegend=True
        ))
        
        # Layout
        fig.update_layout(
            title={
                'text': f'🧠 3D View: {scan_name}<br>Volume: {vol_info["total_cm3"]:.2f} cm³',
                'x': 0.5, 'xanchor': 'center', 'font': {'size': 18, 'color': 'darkblue'}
            },
            scene=dict(
                xaxis_title='Left ← → Right',
                yaxis_title='Posterior ← → Anterior',
                zaxis_title='Inferior ← → Superior',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
                bgcolor='white'
            ),
            width=1100, height=900,
            legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.9)')
        )
        
        # Save HTML
        html_file = VIZ_DIR / f"3D_{scan_name}.html"
        fig.write_html(str(html_file))
        print(f"✅ 3D view saved: {html_file}")
        
        # Show
        fig.show()
        
    except Exception as e:
        print(f"❌ 3D visualization failed: {e}")
    
    print("\n" + "=" * 80)

# ============================================
# CREATE INTERACTIVE DROPDOWN
# ============================================

# Create dropdown options (sorted by volume)
success_sorted = success_df.sort_values('total_cm3')
dropdown_options = [
    f"{row['scan_name']} ({row['total_cm3']:.2f} cm³)" 
    for _, row in success_sorted.iterrows()
]

# Map display names back to scan names
scan_name_map = {
    f"{row['scan_name']} ({row['total_cm3']:.2f} cm³)": row['scan_name']
    for _, row in success_sorted.iterrows()
}

def interactive_viewer(scan_selection):
    """Wrapper for dropdown interaction"""
    scan_name = scan_name_map[scan_selection]
    visualize_hippocampus(scan_name)

print("\n" + "=" * 80)
print("🎮 INTERACTIVE MODE")
print("=" * 80)
print("Use the dropdown below to select any scan!")
print("Scans are sorted by volume (smallest to largest)")
print("\nTip: Try viewing:")
print("  - Smallest volumes (first in list) - check for under-segmentation")
print("  - Largest volumes (last in list) - check for over-segmentation")
print("  - Middle volumes - see typical cases")
print("=" * 80)

# Create interactive widget
interact(
    interactive_viewer,
    scan_selection=Dropdown(
        options=dropdown_options,
        description='Select Scan:',
        style={'description_width': '100px'},
        layout={'width': '500px'}
    )
)

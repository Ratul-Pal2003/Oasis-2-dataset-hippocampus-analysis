# ============================================
# INTERACTIVE HIPPOCAMPUS VIEWER
# Select any scan from menu to visualize
# ============================================

import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from skimage import measure
import plotly.graph_objects as go
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
success_df = success_df.sort_values('total_cm3').reset_index(drop=True)

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

    # Find best slices for each view (matching the corrected notebook)
    # AXIAL (horizontal, top-down view) - slice through y-axis
    best_axial = 0
    max_axial_area = 0
    for y in range(hippo_data.shape[1]):
        area = np.sum(hippo_mask[:, y, :])
        if area > max_axial_area:
            max_axial_area = area
            best_axial = y

    # CORONAL (front-to-back view) - slice through x-axis
    best_coronal = 0
    max_coronal_area = 0
    for x in range(hippo_data.shape[0]):
        area = np.sum(hippo_mask[x, :, :])
        if area > max_coronal_area:
            max_coronal_area = area
            best_coronal = x

    # SAGITTAL (side view) - slice through z-axis
    best_sagittal = 0
    max_sagittal_area = 0
    for z in range(hippo_data.shape[2]):
        area = np.sum(hippo_mask[:, :, z])
        if area > max_sagittal_area:
            max_sagittal_area = area
            best_sagittal = z

    # ============================================
    # 2D VISUALIZATION
    # ============================================

    print("🎨 Creating 2D views...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Row 1: Brain only
    # AXIAL
    axes[0, 0].imshow(np.rot90(brain_data[:, best_axial, :]), cmap='gray', origin='lower')
    axes[0, 0].set_title(f'Brain - Axial (slice {best_axial})', fontsize=12)
    axes[0, 0].axis('off')

    # CORONAL
    axes[0, 1].imshow(np.rot90(brain_data[best_coronal, :, :]), cmap='gray', origin='lower')
    axes[0, 1].set_title(f'Brain - Coronal (slice {best_coronal})', fontsize=12)
    axes[0, 1].axis('off')

    # SAGITTAL
    axes[0, 2].imshow(np.rot90(brain_data[:, :, best_sagittal]), cmap='gray', origin='lower')
    axes[0, 2].set_title(f'Brain - Sagittal (slice {best_sagittal})', fontsize=12)
    axes[0, 2].axis('off')

    # Row 2: Hippocampus overlay
    # AXIAL
    axes[1, 0].imshow(np.rot90(brain_data[:, best_axial, :]), cmap='gray', origin='lower', alpha=0.8)
    axes[1, 0].imshow(np.rot90(hippo_mask[:, best_axial, :]), cmap='Reds', origin='lower', alpha=0.6)
    axes[1, 0].set_title('Hippocampus - Axial', fontsize=12)
    axes[1, 0].axis('off')

    # CORONAL
    axes[1, 1].imshow(np.rot90(brain_data[best_coronal, :, :]), cmap='gray', origin='lower', alpha=0.8)
    axes[1, 1].imshow(np.rot90(hippo_mask[best_coronal, :, :]), cmap='Reds', origin='lower', alpha=0.6)
    axes[1, 1].set_title('Hippocampus - Coronal', fontsize=12)
    axes[1, 1].axis('off')

    # SAGITTAL
    axes[1, 2].imshow(np.rot90(brain_data[:, :, best_sagittal]), cmap='gray', origin='lower', alpha=0.8)
    axes[1, 2].imshow(np.rot90(hippo_mask[:, :, best_sagittal]), cmap='Reds', origin='lower', alpha=0.6)
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
# INTERACTIVE MENU
# ============================================

def display_menu():
    """Display paginated scan selection menu"""
    print("\n" + "=" * 80)
    print("🎮 SELECT A SCAN TO VISUALIZE")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Browse scans by number")
    print("  2. Search by patient ID")
    print("  3. View smallest volume")
    print("  4. View largest volume")
    print("  5. View random scan")
    print("  6. Exit")
    print("=" * 80)

    choice = input("\nEnter your choice (1-6): ").strip()

    if choice == '1':
        browse_scans()
    elif choice == '2':
        search_by_patient()
    elif choice == '3':
        scan = success_df.iloc[0]['scan_name']
        print(f"\n🔍 Showing smallest volume scan: {scan}")
        visualize_hippocampus(scan)
    elif choice == '4':
        scan = success_df.iloc[-1]['scan_name']
        print(f"\n🔍 Showing largest volume scan: {scan}")
        visualize_hippocampus(scan)
    elif choice == '5':
        scan = success_df.sample(1).iloc[0]['scan_name']
        print(f"\n🔍 Showing random scan: {scan}")
        visualize_hippocampus(scan)
    elif choice == '6':
        print("\n👋 Goodbye!")
        return False
    else:
        print("\n❌ Invalid choice. Please try again.")

    return True

def browse_scans():
    """Browse scans with pagination"""
    page_size = 20
    total_pages = (len(success_df) + page_size - 1) // page_size
    current_page = 0

    while True:
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(success_df))

        print("\n" + "=" * 80)
        print(f"SCANS (Page {current_page + 1}/{total_pages})")
        print("=" * 80)
        print(f"{'#':<5} {'Scan Name':<20} {'Patient':<10} {'Session':<10} {'Volume (cm³)':<15}")
        print("-" * 80)

        for i in range(start_idx, end_idx):
            row = success_df.iloc[i]
            print(f"{i+1:<5} {row['scan_name']:<20} {row['patient_id']:<10} {row['session']:<10} {row['total_cm3']:<15.2f}")

        print("=" * 80)
        print("\nOptions: [N]ext page, [P]revious page, [#]Select scan number, [B]ack to main menu")

        choice = input("Enter your choice: ").strip().lower()

        if choice == 'n' and current_page < total_pages - 1:
            current_page += 1
        elif choice == 'p' and current_page > 0:
            current_page -= 1
        elif choice == 'b':
            break
        elif choice.isdigit():
            scan_num = int(choice) - 1
            if 0 <= scan_num < len(success_df):
                scan_name = success_df.iloc[scan_num]['scan_name']
                print(f"\n🔍 Visualizing scan #{scan_num + 1}: {scan_name}")
                visualize_hippocampus(scan_name)
                break
            else:
                print(f"\n❌ Invalid scan number. Please enter 1-{len(success_df)}")
        else:
            print("\n❌ Invalid choice. Please try again.")

def search_by_patient():
    """Search scans by patient ID"""
    patient_list = success_df['patient_id'].unique()
    print("\n" + "=" * 80)
    print("SEARCH BY PATIENT ID")
    print("=" * 80)
    print(f"Available patient IDs: {', '.join(sorted(patient_list))}")
    print("=" * 80)

    patient_id = input("\nEnter patient ID (e.g., 0001): ").strip()

    patient_scans = success_df[success_df['patient_id'] == patient_id]

    if len(patient_scans) == 0:
        print(f"\n❌ No scans found for patient {patient_id}")
        return

    print(f"\n🔍 Found {len(patient_scans)} scan(s) for patient {patient_id}:")
    print("-" * 80)
    print(f"{'#':<5} {'Scan Name':<20} {'Session':<10} {'Volume (cm³)':<15}")
    print("-" * 80)

    for i, (_, row) in enumerate(patient_scans.iterrows()):
        print(f"{i+1:<5} {row['scan_name']:<20} {row['session']:<10} {row['total_cm3']:<15.2f}")

    if len(patient_scans) == 1:
        scan_name = patient_scans.iloc[0]['scan_name']
        print(f"\n🔍 Visualizing: {scan_name}")
        visualize_hippocampus(scan_name)
    else:
        choice = input(f"\nSelect scan (1-{len(patient_scans)}) or [B]ack: ").strip()
        if choice.lower() != 'b' and choice.isdigit():
            scan_idx = int(choice) - 1
            if 0 <= scan_idx < len(patient_scans):
                scan_name = patient_scans.iloc[scan_idx]['scan_name']
                print(f"\n🔍 Visualizing: {scan_name}")
                visualize_hippocampus(scan_name)

# ============================================
# MAIN LOOP
# ============================================

if __name__ == "__main__":
    print("\n💡 Tip: Close the visualization windows to continue browsing.")
    print("💡 3D visualizations will open in your web browser automatically.")

    while True:
        if not display_menu():
            break

    print("\n" + "=" * 80)
    print("Thank you for using the Hippocampus Viewer!")
    print("=" * 80)

"""
Tools_Generate_Images.py - Generate syntax-highlighted code screenshots for the article

Uses Pygments to render code snippets as PNG images.
Updated to reflect the final "Zemax Native" Thermal Analysis implementation.
"""

import os

# Check and install dependencies
try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import ImageFormatter
except ImportError:
    print("Installing pygments...")
    os.system("pip install pygments pillow")
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import ImageFormatter


def generate_code_image(code, output_path, style_name="monokai", font_size=28, line_numbers=True):
    """
    Generate code screenshot
    """
    formatter = ImageFormatter(
        style=style_name,
        font_size=font_size,
        line_numbers=line_numbers,
        line_number_bg="#1e1e1e",
        line_number_fg="#858585",
        line_number_separator=True,
        image_pad=20,
        line_pad=8,
    )
    
    result = highlight(code, PythonLexer(), formatter)
    
    with open(output_path, 'wb') as f:
        f.write(result)
    
    print(f"Generated: {output_path}")


# ============================================================
# Snippet 1: Core Analysis Function (Native Zemax Analysis)
# ============================================================
code_core_function = '''def get_spot_rms_from_analysis(TheSystem, ZOSAPI):
    """
    Run Standard Spot Analysis and retrieve RMS Radius.
    This mimics opening the "Spot Diagram" window in GUI.
    """
    # 1. Open Analysis Window
    spot = TheSystem.Analyses.New_Analysis(ZOSAPI.Analysis.AnalysisIDM.StandardSpot)
    
    # 2. Run Analysis (Waits for full raytrace)
    spot.ApplyAndWaitForCompletion()
    
    # 3. Retrieve Results
    results = spot.GetResults()
    
    # 4. Parse Output (RMS Radius is in the header/text report)
    report_file = os.path.join(TheSystem.TheApplication.SamplesDir, "temp_spot.txt")
    results.GetTextFile(report_file)
    
    rms_val = 0.0
    with open(report_file, 'r', encoding='utf-16') as f:
        for line in f:
            if "RMS radius" in line:
                # Format: "RMS radius    :  4.987 microns"
                parts = line.split(':')
                rms_val = float(parts[1].strip().split(' ')[0])
                break
                
    spot.Close()
    return rms_val
'''

# ============================================================
# Snippet 2: Connecting to Zemax
# ============================================================
code_connect = '''# Boilerplate to connect to running Zemax instance
import clr, os, winreg

# ... (Registry lookup code omitted for brevity) ...

# Initialize ZOS-API
import ZOSAPI_NetHelper
ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
import ZOSAPI

# Create Connection
TheConnection = ZOSAPI.ZOSAPI_Connection()
TheApplication = TheConnection.CreateNewApplication()
TheSystem = TheApplication.PrimarySystem

print(f"Connected to: {TheSystem.SystemName}")
'''

# ============================================================
# Snippet 3: Thermal Sweep Logic (Using MCE)
# ============================================================
code_thermal_sweep = '''# Setup Multi-Configuration for Thermal Analysis
MCE = TheSystem.MCE
temps = [20, 50, 80]

# Ensure we have enough configurations
while MCE.NumberOfConfigurations < len(temps):
    MCE.AddConfiguration(True)

# Set "TEMP" Operand
op = MCE.GetOperandAt(1)
op.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)

for i, t in enumerate(temps):
    op.GetOperandCell(i + 1).DoubleValue = float(t)

# Run Sweep
print("\\nRunning Thermal Sweep...")
for i, t in enumerate(temps):
    config = i + 1
    MCE.SetCurrentConfiguration(config)
    
    # Get physical result from Analysis
    rms = get_spot_rms_from_analysis(TheSystem, ZOSAPI)
    print(f"  T={t}C (Config {config}): RMS Spot = {rms:.4f} microns")
'''

# ============================================================
# Snippet 4: Actual Execution Output
# ============================================================
code_output = '''============================================================
Task: Thermal Analysis via Spot Diagram Analysis
============================================================
Loaded: A SIMPLE COOKE TRIPLET.
Setting up Environment...
  AdjustIndexToEnvironment: True

Running Sweep...
  T=20C (Config 1): RMS Spot = 4.9879 microns
  T=50C (Config 2): RMS Spot = 4.5133 microns
  T=80C (Config 3): RMS Spot = 5.2616 microns
'''


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    print("=" * 60)
    print("Generating Article Code Screenshots")
    print("=" * 60)
    
    images = [
        (code_core_function, "code_01_core_function.png", "Core Function"),
        (code_connect, "code_02_connect.png", "Zemax Connection"),
        (code_thermal_sweep, "code_03_thermal_sweep.png", "Thermal Sweep Logic"),
        (code_output, "code_04_output.png", "Execution Output"),
    ]
    
    for code, filename, desc in images:
        output_path = os.path.join(images_dir, filename)
        print(f"\nGenerating {desc}...")
        generate_code_image(
            code, 
            output_path, 
            style_name="monokai",
            font_size=24,
            line_numbers=True
        )
    
    print("\n" + "=" * 60)
    print("All images generated successfully!")
    print(f"Location: {script_dir}")

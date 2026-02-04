
"""
08_Monte_Carlo_Tolerance.py - Monte Carlo Tolerance Analysis

Task:
1. Connect to Zemax and load Cooke Triplet.
2. Insert Coordinate Breaks to simulate element tolerances (Tilt/Decenter).
3. Run 1000 Monte Carlo simulations:
   - Randomize Temperature (-40 to 85C)
   - Randomize Lens Tolerances (Dx, Dy, Tx, Ty) for 3 lenses.
   - Run Quick Focus.
   - Measure RMS Spot Radius.
4. Save data to 'dataset_v2_tolerance.csv'.
"""

import clr
import os
import sys
import winreg
import random
import csv
import time
import numpy as np

# --- ZOS-API Connection Class (Reused) ---
class PythonStandaloneApplication:
    def __init__(self):
        self.TheConnection = None
        self.TheApplication = None
        self.TheSystem = None
        self.ZOSAPI = None
        
        try:
            aKey = winreg.OpenKey(winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER), r"Software\Zemax", 0, winreg.KEY_READ)
            zemaxData = winreg.QueryValueEx(aKey, 'ZemaxRoot')
            winreg.CloseKey(aKey)
            self.zemaxDir = zemaxData[0]
            netHelperPath = os.path.join(self.zemaxDir, r'ZOS-API\Libraries\ZOSAPI_NetHelper.dll')
            clr.AddReference(netHelperPath)
            import ZOSAPI_NetHelper
            ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
            zemaxDirectory = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
            clr.AddReference(os.path.join(zemaxDirectory, "ZOSAPI.dll"))
            clr.AddReference(os.path.join(zemaxDirectory, "ZOSAPI_Interfaces.dll"))
            import ZOSAPI
            self.ZOSAPI = ZOSAPI
            self.TheConnection = ZOSAPI.ZOSAPI_Connection()
            self.TheApplication = self.TheConnection.CreateNewApplication()
            self.TheSystem = self.TheApplication.PrimarySystem
        except Exception as e:
            print(f"Connection failed: {e}")
            sys.exit(1)

    def close(self):
        if self.TheApplication:
            self.TheApplication.CloseApplication()

# --- Helper Functions ---

def setup_coordinate_breaks(TheSystem, ZOSAPI):
    """
    Inserts Coordinate Breaks (CB) around Lens 1, 2, and 3.
    Assumes original surface structure:
    1-2: Lens 1
    3-4: Lens 2
    5-6: Lens 3
    
    Returns a dict of surface indices for the perturbation CBs.
    """
    LDE = TheSystem.LDE
    
    print("Inserting Coordinate Breaks for Tolerance Analysis...")
    
    # Process Reverse Order to maintain indices for lower lenses
    
    # --- Lens 3 (Orig 5-6) ---
    # Insert Restore CB after Surf 6 -> New Index 7
    cb_l3_out = LDE.InsertNewSurfaceAt(7)
    cb_l3_out.ChangeType(cb_l3_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l3_out.Comment = "CB_L3_Out"
    
    # Insert Perturb CB before Surf 5 -> New Index 5
    cb_l3_in = LDE.InsertNewSurfaceAt(5)
    cb_l3_in.ChangeType(cb_l3_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l3_in.Comment = "CB_L3_In"
    
    # Setup Pickup Solves for L3 Out (Surf 8 now)
    # Indices: 1..4, 5(CB), 6(L3F), 7(L3B), 8(CB)
    # Verify index 8
    cb_l3_out_idx = 8
    cb_l3_in_idx = 5
    
    # --- Lens 2 (Orig 3-4) ---
    # Insert Restore CB after Surf 4 -> New Index 5 (pushes L3 down)
    cb_l2_out = LDE.InsertNewSurfaceAt(5)
    cb_l2_out.ChangeType(cb_l2_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l2_out.Comment = "CB_L2_Out"
    
    # Insert Perturb CB before Surf 3 -> New Index 3
    cb_l2_in = LDE.InsertNewSurfaceAt(3)
    cb_l2_in.ChangeType(cb_l2_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l2_in.Comment = "CB_L2_In"
    
    # Indices update:
    # L2 In: 3
    # L2 Out: 6
    # L3 In: 5 + 2 = 7 ?? No.
    # Let's trace L3 indices.
    # Before L2 ops: L3 In=5, L3 Out=8.
    # Insert at 5 (L2 Out): L3 In becomes 6, L3 Out becomes 9.
    # Insert at 3 (L2 In): L3 In becomes 7, L3 Out becomes 10.
    
    # --- Lens 1 (Orig 1-2) ---
    # Insert Restore CB after Surf 2 -> New Index 3
    cb_l1_out = LDE.InsertNewSurfaceAt(3)
    cb_l1_out.ChangeType(cb_l1_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l1_out.Comment = "CB_L1_Out"
    
    # Insert Perturb CB before Surf 1 -> New Index 1
    cb_l1_in = LDE.InsertNewSurfaceAt(1)
    cb_l1_in.ChangeType(cb_l1_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l1_in.Comment = "CB_L1_In"
    
    # Final Indices Calculation
    # L1 In: 1
    # L1 Out: 4
    
    # L2 In: Was 3. After L1 ops (insert 2 before it): 3 + 2 = 5.
    # L2 Out: Was 6. After L1 ops: 6 + 2 = 8.
    
    # L3 In: Was 7. After L1 ops: 7 + 2 = 9.
    # L3 Out: Was 10. After L1 ops: 10 + 2 = 12.
    
    # Verify and Set Pickups
    indices = {
        'L1': {'in': 1, 'out': 4},
        'L2': {'in': 5, 'out': 8},
        'L3': {'in': 9, 'out': 12}
    }
    
    for key, val in indices.items():
        s_in = LDE.GetSurfaceAt(val['in'])
        s_out = LDE.GetSurfaceAt(val['out'])
        
        # Params: 1:DecenterX, 2:DecenterY, 3:TiltX, 4:TiltY, 5:TiltZ
        for param in range(1, 6): # 1 to 5
            # Set Pickup on Output CB to reverse Input CB
            # Use getattr to get Enum by name to avoid int addition issues
            col_enum = getattr(ZOSAPI.Editors.LDE.SurfaceColumn, f"Par{param}")
            
            cell = s_out.GetSurfaceCell(col_enum)
            solve = cell.CreateSolveType(ZOSAPI.Editors.SolveType.SurfacePickup)
            solve._S_SurfacePickup.SourceSurface = val['in']
            solve._S_SurfacePickup.ScaleFactor = -1.0
            cell.SetSolveData(solve)
            
    return indices

def get_spot_rms(TheSystem, ZOSAPI):
    spot = TheSystem.Analyses.New_Analysis(ZOSAPI.Analysis.AnalysisIDM.StandardSpot)
    spot.ApplyAndWaitForCompletion()
    results = spot.GetResults()
    
    # Robust method to get RMS from text results (since API result object sometimes tricky)
    # Actually, try the API method first for speed
    # rms = results.GetResult(0).GetValue() # Often not populated for StandardSpot
    
    # Fallback to file parsing which is reliable
    temp_file = os.path.join(TheSystem.TheApplication.SamplesDir, f"spot_res_{random.randint(0,10000)}.txt")
    results.GetTextFile(temp_file)
    
    rms_val = float('nan')
    if os.path.exists(temp_file):
        try:
            with open(temp_file, 'r', encoding='utf-16') as f:
                content = f.read()
            for line in content.split('\n'):
                if "RMS" in line and "GEO" not in line: # RMS Radius
                     parts = line.split(':')
                     if len(parts) > 1:
                         val_str = parts[1].strip().split()[0]
                         rms_val = float(val_str)
                         break
        except:
            pass
        try:
            os.remove(temp_file)
        except: pass
        
    spot.Close()
    return rms_val

def run_quick_focus(TheSystem, ZOSAPI):
    qf = TheSystem.Tools.OpenQuickFocus()
    if qf is None: return # Safety check
    
    # Fix for Python.NET 3.0: Use explicit Enum
    qf.Criterion = ZOSAPI.Tools.General.QuickFocusCriterion.SpotSizeRadial
    qf.UseCentroid = True
    qf.RunAndWaitForCompletion()
    qf.Close()

def main():
    print("=" * 60)
    print("Monte Carlo Tolerance Analysis (Thermal + Manufacturing)")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lens_file = os.path.join(script_dir, "models", "Cooke_Triplet_Base.zmx")
    
    zos = PythonStandaloneApplication()
    TheSystem = zos.TheSystem
    ZOSAPI = zos.ZOSAPI
    
    if not os.path.exists(lens_file):
        print("Lens file not found.")
        return

    # 1. Load File
    TheSystem.LoadFile(lens_file, False)
    print(f"Loaded: {TheSystem.SystemName}")
    
    # 2. Setup CBs
    cb_indices = setup_coordinate_breaks(TheSystem, ZOSAPI)
    print("Coordinate Breaks inserted.")
    
    # 3. Setup MCE for Temperature (Config 2)
    MCE = TheSystem.MCE
    if MCE.NumberOfConfigurations < 2:
        MCE.AddConfiguration(True)
    
    # Setup Thermal Pickup/Env
    TheSystem.SystemData.Environment.AdjustIndexToEnvironment = True
    
    # Use MCE Operand 1 for Temperature
    op_temp = MCE.GetOperandAt(1)
    op_temp.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
    MCE.SetCurrentConfiguration(2)
    
    # 4. Monte Carlo Loop
    output_csv = os.path.join(script_dir, "models", "dataset_v2_tolerance.csv")
    
    print("\nStarting Monte Carlo Simulation (1000 runs)...")
    
    headers = [
        "Temp", 
        "L1_Dx", "L1_Dy", "L1_Tx", "L1_Ty",
        "L2_Dx", "L2_Dy", "L2_Tx", "L2_Ty",
        "L3_Dx", "L3_Dy", "L3_Tx", "L3_Ty",
        "RMS_Spot"
    ]
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        start_time = time.time()
        
        for i in range(1000):
            try:
                # A. Generate Random Variables
                temp = random.uniform(-40, 85)
                
                # Tolerances: Dx/Dy +/- 0.2mm, Tx/Ty +/- 1.0 deg
                tols = {}
                for lens in ['L1', 'L2', 'L3']:
                    tols[lens] = [
                        random.uniform(-0.2, 0.2), # Dx
                        random.uniform(-0.2, 0.2), # Dy
                        random.uniform(-1.0, 1.0), # Tx
                        random.uniform(-1.0, 1.0)  # Ty
                    ]
                
                # B. Apply Variables
                # Temperature
                op_temp.GetOperandCell(2).DoubleValue = temp
                
                # Lens Tolerances
                LDE = TheSystem.LDE
                for lens_name, values in tols.items():
                    idx = cb_indices[lens_name]['in']
                    surf = LDE.GetSurfaceAt(idx)
                    
                    # Param 1: Decenter X, 2: Decenter Y, 3: Tilt X, 4: Tilt Y
                    surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par1).DoubleValue = values[0]
                    surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par2).DoubleValue = values[1]
                    surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par3).DoubleValue = values[2]
                    surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par4).DoubleValue = values[3]
                
                # C. Quick Focus
                run_quick_focus(TheSystem, ZOSAPI)
                
                # D. Ray Trace / Measure
                rms = get_spot_rms(TheSystem, ZOSAPI)
                
                # E. Log
                row = [temp]
                for lens in ['L1', 'L2', 'L3']:
                    row.extend(tols[lens])
                row.append(rms)
                
                writer.writerow(row)
                
                if (i+1) % 50 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Progress: {i+1}/1000 | Last RMS: {rms:.4f} | Time: {elapsed:.1f}s")
                    
            except Exception as e:
                print(f"  Warning: Run {i+1} failed - {e}")
                continue

    print(f"\nCompleted. Data saved to {output_csv}")
    zos.close()

if __name__ == "__main__":
    main()

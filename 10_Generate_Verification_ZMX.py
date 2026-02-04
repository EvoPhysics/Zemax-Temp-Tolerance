
"""
10_Generate_Verification_ZMX.py - Generate a Verification ZMX File

Task:
1. Load Cooke_Triplet_Base.zmx
2. Insert Coordinate Breaks (same logic as 08_Monte_Carlo_Tolerance.py)
3. Apply specific parameters from Dataset Case #2 (Line 3 in CSV)
4. Save as 'models/Verification_Case_2.zmx'
"""

import clr
import os
import sys
import winreg

# --- Parameters from Case #2 ---
# CSV Line 3: -1.2366, 0.0023, 0.1441, -0.2969, 0.8707, ...
CASE_DATA = {
    'Temp': -1.236637968475364,
    'L1': [0.0023166679056995376, 0.1440919409184106, -0.2969102984595793, 0.8707434698093544],
    'L2': [-0.061335464333547945, 0.18522653107644277, 0.5743563767047353, -0.6133877235975889],
    'L3': [0.08080368940444094, -0.05430065208096374, -0.2097173040200453, -0.3410756916495883],
    'Expected_RMS': 28.9146084
}

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

def setup_coordinate_breaks(TheSystem, ZOSAPI):
    """Inserts Coordinate Breaks (Same logic as 08 script)"""
    LDE = TheSystem.LDE
    print("Inserting Coordinate Breaks...")
    
    # --- Lens 3 ---
    cb_l3_out = LDE.InsertNewSurfaceAt(7)
    cb_l3_out.ChangeType(cb_l3_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l3_out.Comment = "CB_L3_Out"
    
    cb_l3_in = LDE.InsertNewSurfaceAt(5)
    cb_l3_in.ChangeType(cb_l3_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l3_in.Comment = "CB_L3_In"
    
    # --- Lens 2 ---
    cb_l2_out = LDE.InsertNewSurfaceAt(5)
    cb_l2_out.ChangeType(cb_l2_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l2_out.Comment = "CB_L2_Out"
    
    cb_l2_in = LDE.InsertNewSurfaceAt(3)
    cb_l2_in.ChangeType(cb_l2_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l2_in.Comment = "CB_L2_In"
    
    # --- Lens 1 ---
    cb_l1_out = LDE.InsertNewSurfaceAt(3)
    cb_l1_out.ChangeType(cb_l1_out.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l1_out.Comment = "CB_L1_Out"
    
    cb_l1_in = LDE.InsertNewSurfaceAt(1)
    cb_l1_in.ChangeType(cb_l1_in.GetSurfaceTypeSettings(ZOSAPI.Editors.LDE.SurfaceType.CoordinateBreak))
    cb_l1_in.Comment = "CB_L1_In"
    
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
            col_enum = getattr(ZOSAPI.Editors.LDE.SurfaceColumn, f"Par{param}")
            cell = s_out.GetSurfaceCell(col_enum)
            solve = cell.CreateSolveType(ZOSAPI.Editors.SolveType.SurfacePickup)
            solve._S_SurfacePickup.SourceSurface = val['in']
            solve._S_SurfacePickup.ScaleFactor = -1.0
            cell.SetSolveData(solve)
            
    return indices

def main():
    print("=" * 60)
    print("Generating Verification ZMX File (Case #2)")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lens_file = os.path.join(script_dir, "models", "Cooke_Triplet_Base.zmx")
    save_file = os.path.join(script_dir, "models", "Verification_Case_2.zmx")
    
    zos = PythonStandaloneApplication()
    TheSystem = zos.TheSystem
    ZOSAPI = zos.ZOSAPI
    
    if not os.path.exists(lens_file):
        print("Error: Base lens file not found.")
        return

    # 1. Load Base File
    TheSystem.LoadFile(lens_file, False)
    print(f"Loaded Base: {TheSystem.SystemName}")
    
    # 2. Insert CBs
    cb_indices = setup_coordinate_breaks(TheSystem, ZOSAPI)
    
    # 3. Apply Parameters
    print("\nApplying Parameters...")
    
    # Temperature
    print(f"  Setting Temperature: {CASE_DATA['Temp']:.4f} C")
    TheSystem.SystemData.Environment.AdjustIndexToEnvironment = True
    
    MCE = TheSystem.MCE
    if MCE.NumberOfConfigurations < 2:
        MCE.AddConfiguration(True)
    
    op_temp = MCE.GetOperandAt(1)
    op_temp.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
    op_temp.GetOperandCell(2).DoubleValue = CASE_DATA['Temp']
    MCE.SetCurrentConfiguration(2)
    
    # Lens Tolerances
    LDE = TheSystem.LDE
    for lens_name, values in CASE_DATA.items():
        if lens_name not in cb_indices: continue
        
        print(f"  Setting {lens_name} Tolerances: {values}")
        idx = cb_indices[lens_name]['in']
        surf = LDE.GetSurfaceAt(idx)
        
        # Param 1: Dx, 2: Dy, 3: Tx, 4: Ty
        surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par1).DoubleValue = values[0]
        surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par2).DoubleValue = values[1]
        surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par3).DoubleValue = values[2]
        surf.GetSurfaceCell(ZOSAPI.Editors.LDE.SurfaceColumn.Par4).DoubleValue = values[3]

    # 4. Save File
    print(f"\nSaving to: {save_file}")
    TheSystem.SaveAs(save_file)
    
    print("Done! You can now open this file in Zemax to verify the spot size.")
    print(f"Expected RMS Spot Radius: {CASE_DATA['Expected_RMS']} microns")
    
    zos.close()

if __name__ == "__main__":
    main()

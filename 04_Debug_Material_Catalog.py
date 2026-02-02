"""
04_auto_thermal_analysis.py - Fully Automated Thermal Analysis with Catalog Verification

Task:
1. Load Lens File
2. Automatically verify thermal data (TCE, D0, dn/dT) from Zemax Material Catalogs
3. Perform Multi-Configuration Thermal Analysis
4. Output results proving thermal effects are calculated based on DB data
"""

import clr
import os
import sys
import winreg
import traceback

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
        print("Successfully connected to Zemax OpticStudio!")

    def load_file(self, filepath):
        """Load a lens file from absolute path"""
        if os.path.exists(filepath):
            self.TheSystem.LoadFile(filepath, False)
            return True
        return False

    def close(self):
        if self.TheApplication:
            self.TheApplication.CloseApplication()

def verify_and_load_catalogs(TheSystem):
    """
    Ensure SCHOTT and other essential catalogs are loaded.
    """
    print("\n" + "-" * 60)
    print("VERIFYING MATERIAL CATALOGS")
    print("-" * 60)
    
    mc_data = TheSystem.SystemData.MaterialCatalogs
    
    # Check if SCHOTT is loaded
    catalogs = mc_data.GetCatalogsInUse()
    print(f"  Current Catalogs: {list(catalogs)}")
    
    if "SCHOTT" not in catalogs:
        print("  Adding 'SCHOTT' catalog...")
        mc_data.AddCatalog("SCHOTT")
    
    # Reload to ensure availability
    # mc_data.ReloadCatalogs() # Not always available/needed, AddCatalog triggers update

def inspect_surface_materials(TheSystem):
    """
    Inspect each surface's material using the Materials Catalog Tool.
    This proves Python accesses the internal database.
    """
    print("\n" + "-" * 60)
    print("INSPECTING SURFACE MATERIALS (DATABASE CHECK)")
    print("-" * 60)
    
    LDE = TheSystem.LDE
    tools = TheSystem.Tools
    cat_tool = tools.OpenMaterialsCatalog()
    
    for i in range(1, LDE.NumberOfSurfaces): # Skip Object
        s = LDE.GetSurfaceAt(i)
        mat_name = s.Material
        
        # Skip Air
        if not mat_name or mat_name.upper() == "AIR":
            # For Air, we set TCE manually to simulate housing
            s.TCE = 23.0
            print(f"  Surf {i} [AIR]: Set Housing TCE = 23.0")
            continue
            
        # For Glass, query the database
        # We need to find which catalog this material belongs to
        # Simplification: Try SCHOTT first, or just set SelectedMaterial and let tool find it?
        # The tool usually requires SelectedCatalog AND SelectedMaterial.
        
        # Heuristic: Try to find the material in loaded catalogs
        found = False
        catalogs = TheSystem.SystemData.MaterialCatalogs.GetCatalogsInUse()
        
        for cat in catalogs:
            cat_tool.SelectedCatalog = cat
            cat_tool.SelectedMaterial = mat_name
            if cat_tool.SelectedMaterial == mat_name: # Verification
                # Found it!
                found = True
                print(f"  Surf {i} [{mat_name}] found in '{cat}'")
                
                # Check Thermal Data
                tce = cat_tool.TCE
                d0 = cat_tool.D0
                
                print(f"    -> Database TCE: {tce}")
                print(f"    -> Database D0:  {d0}")
                
                if d0 == 0 and tce == 0:
                    print("    WARNING: Material has no thermal data!")
                else:
                    print("    OK: Thermal data present.")
                break
        
        if not found:
            print(f"  Surf {i} [{mat_name}]: NOT FOUND in loaded catalogs!")

    cat_tool.Close()

def run_mce_analysis(TheSystem, ZOSAPI, temps):
    """
    Run the Multi-Configuration Thermal Analysis
    """
    print("\n" + "-" * 60)
    print("RUNNING THERMAL ANALYSIS")
    print("-" * 60)
    
    # 1. Setup Environment
    env = TheSystem.SystemData.Environment
    env.AdjustIndexToEnvironment = True
    print(f"  AdjustIndexToEnvironment: {env.AdjustIndexToEnvironment}")
    
    # 2. Setup MCE
    MCE = TheSystem.MCE
    while MCE.NumberOfConfigurations < len(temps):
        MCE.AddConfiguration(True)
        
    op = MCE.GetOperandAt(1)
    op.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
    
    for i, t in enumerate(temps):
        cell = op.GetOperandCell(i + 1)
        cell.DoubleValue = float(t)
        print(f"  Config {i+1}: Temp = {t} C")
        
    # 3. Analyze
    MFE = TheSystem.MFE
    rsce = MFE.AddOperand()
    rsce.ChangeType(ZOSAPI.Editors.MFE.MeritOperandType.RSCE)
    
    results = []
    for i, t in enumerate(temps):
        MCE.SetCurrentConfiguration(i + 1)
        MFE.CalculateMeritFunction()
        spot = rsce.Value * 1000.0
        results.append(spot)
        print(f"    -> Spot RMS: {spot:.4f} um")
        
    MFE.RemoveOperandAt(MFE.NumberOfOperands)
    return results

def main():
    print("=" * 60)
    print("Task: Auto-Call Material Database & Thermal Analysis")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lens_file = os.path.join(script_dir, "models", "Cooke_Triplet_Base.zmx")
    
    zos = PythonStandaloneApplication()
    if zos.load_file(lens_file):
        print(f"Loaded: {zos.TheSystem.SystemName}")
        
        # 1. Ensure Catalogs are loaded
        verify_and_load_catalogs(zos.TheSystem)
        
        # 2. Verify Thermal Data from Database
        inspect_surface_materials(zos.TheSystem)
        
        # 3. Run Analysis
        temps = [20, 50, 80]
        results = run_mce_analysis(zos.TheSystem, zos.ZOSAPI, temps)
        
        # 4. Summary
        diff = max(results) - min(results)
        print("\n" + "=" * 60)
        if diff > 0.0001:
            print(f"SUCCESS: Thermal changes detected! (Range: {diff:.4f} um)")
        else:
            print(f"RESULT: No change detected (Range: {diff:.4f} um).")
            print("If you see 'Thermal data present' above, try manually saving the lens file")
            print("once with 'Adjust Index to Environment' checked to force internal updates.")
        print("=" * 60)
        
    zos.close()

if __name__ == "__main__":
    main()

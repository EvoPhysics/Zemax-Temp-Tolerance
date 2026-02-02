"""
06_Thermal_Analysis_Sweep_0_100.py - Thermal Analysis Sweep 0-100C

Task:
Perform a temperature sweep from 0C to 100C in 10C steps.
Uses a single configuration (Config 2) and updates it iteratively to avoid MCE limits.
Config 1 is kept at 20C as a reference.
"""

import clr
import os
import sys
import winreg
import time

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

def setup_environment(TheSystem):
    print("Setting up Environment...")
    env = TheSystem.SystemData.Environment
    env.AdjustIndexToEnvironment = True
    print(f"  AdjustIndexToEnvironment: {env.AdjustIndexToEnvironment}")
    
    # Set Air TCE
    LDE = TheSystem.LDE
    for i in range(1, LDE.NumberOfSurfaces):
        s = LDE.GetSurfaceAt(i)
        if s.Material.upper() == "" or s.Material.upper() == "AIR":
            s.TCE = 23.0

def get_spot_rms_from_analysis(TheSystem, ZOSAPI):
    spot = TheSystem.Analyses.New_Analysis(ZOSAPI.Analysis.AnalysisIDM.StandardSpot)
    spot.ApplyAndWaitForCompletion()
    results = spot.GetResults()
    
    report_file = os.path.join(TheSystem.TheApplication.SamplesDir, "temp_spot_report_loop.txt")
    if os.path.exists(report_file):
        try: os.remove(report_file)
        except: pass
        
    results.GetTextFile(report_file)
    rms_val = -1.0
    
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r', encoding='utf-16') as f:
                content = f.read()
        except:
            with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
        for line in content.split('\n'):
            if "RMS" in line and ":" in line:
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        val_str = parts[1].strip().split(' ')[0]
                        rms_val = float(val_str)
                        break
                    except: pass
        os.remove(report_file)
    spot.Close()
    return rms_val

def main():
    print("=" * 60)
    print("Task: Thermal Analysis Sweep 0-100C")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lens_file = os.path.join(script_dir, "models", "Cooke_Triplet_Base.zmx")
    
    zos = PythonStandaloneApplication()
    TheSystem = zos.TheSystem
    ZOSAPI = zos.ZOSAPI
    
    if os.path.exists(lens_file):
        print(f"DEBUG: Found lens file at {lens_file}")
        TheSystem.LoadFile(lens_file, False)
        print(f"Loaded: {TheSystem.SystemName}")
        
        setup_environment(TheSystem)
        
        MCE = TheSystem.MCE
        
        # Add Config 2 (Working Config)
        if MCE.NumberOfConfigurations < 2:
            MCE.AddConfiguration(True)
            
        op = MCE.GetOperandAt(1)
        op.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
        
        # Set Config 1 (Reference) to 20C
        op.GetOperandCell(1).DoubleValue = 20.0
        
        sweep_temps = list(range(0, 101, 10))
        
        print("\nRunning Sweep...")
        print("-" * 40)
        print(f"{'Temp (C)':<10} | {'RMS Spot (microns)':<20}")
        print("-" * 40)
        
        for t in sweep_temps:
            # Update Config 2
            op.GetOperandCell(2).DoubleValue = float(t)
            
            # Activate Config 2
            MCE.SetCurrentConfiguration(2)
            
            # Run Analysis
            rms = get_spot_rms_from_analysis(TheSystem, ZOSAPI)
            print(f"{t:<10} | {rms:.4f}")
            
    else:
        print(f"ERROR: Lens file not found")

    zos.close()

if __name__ == "__main__":
    main()

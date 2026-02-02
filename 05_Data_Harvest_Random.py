"""
10_Data_Harvest_Random.py - Task A: Mass Production Data

Features:
1. Generates 200 random temperature points between -40C and 85C.
2. Uses iterative MCE update (Config 2) to collect RMS Spot Radius.
3. Saves data to 'dataset_v1.csv'.
"""

import clr
import os
import sys
import winreg
import time
import csv
import numpy as np

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
    # print("Setting up Environment...")
    env = TheSystem.SystemData.Environment
    env.AdjustIndexToEnvironment = True
    # print(f"  AdjustIndexToEnvironment: {env.AdjustIndexToEnvironment}")
    
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
    
    report_file = os.path.join(TheSystem.TheApplication.SamplesDir, "temp_harvest_spot.txt")
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
    print("Task A: The Harvest (Random Sampling)")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lens_file = os.path.join(script_dir, "models", "Cooke_Triplet_Base.zmx")
    csv_file = os.path.join(script_dir, "models", "dataset_v1.csv")
    
    zos = PythonStandaloneApplication()
    TheSystem = zos.TheSystem
    ZOSAPI = zos.ZOSAPI
    
    if os.path.exists(lens_file):
        print(f"Loading lens: {lens_file}")
        TheSystem.LoadFile(lens_file, False)
        
        setup_environment(TheSystem)
        
        MCE = TheSystem.MCE
        
        # Add Config 2 (Working Config)
        if MCE.NumberOfConfigurations < 2:
            MCE.AddConfiguration(True)
            
        op = MCE.GetOperandAt(1)
        op.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
        
        # Set Config 1 (Reference) to 20C
        op.GetOperandCell(1).DoubleValue = 20.0
        
        # Generate Random Data
        np.random.seed(42) # Reproducibility
        temps = np.random.uniform(low=-40, high=85, size=200)
        
        print(f"\nStarting collection of {len(temps)} samples...")
        print("-" * 40)
        
        data_rows = []
        
        start_time = time.time()
        
        for i, t in enumerate(temps):
            # Update Config 2
            op.GetOperandCell(2).DoubleValue = float(t)
            
            # Activate Config 2
            MCE.SetCurrentConfiguration(2)
            
            # Run Analysis
            rms = get_spot_rms_from_analysis(TheSystem, ZOSAPI)
            
            data_rows.append([t, rms])
            
            # Progress log every 10 samples
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(temps)}] T={t:.2f}C -> RMS={rms:.4f} um")
                
        duration = time.time() - start_time
        print("-" * 40)
        print(f"Collection complete in {duration:.2f} seconds.")
        
        # Save to CSV
        print(f"\nSaving to {csv_file}...")
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Temperature', 'Spot_Radius'])
            writer.writerows(data_rows)
            
        print("Done!")
        
        # Validation
        print("\nVerifying data integrity...")
        valid = True
        min_rms = min(row[1] for row in data_rows)
        if min_rms <= 0:
            print(f"ERROR: Found non-positive spot size: {min_rms}")
            valid = False
        
        if valid:
            print("PASSED: All spot sizes are positive.")
            
    else:
        print(f"ERROR: Lens file not found")

    zos.close()

if __name__ == "__main__":
    main()

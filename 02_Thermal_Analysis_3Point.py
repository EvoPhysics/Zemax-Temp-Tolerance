"""
05_analysis_thermal_test.py - Thermal Analysis using Standard Spot Analysis

Task:
1. Load Lens File
2. Setup Environment & Thermal Data
3. Use 'StandardSpot' Analysis (instead of MFE) to measure RMS Radius
   (This mimics the user opening the Spot Diagram window)
4. Verify if this detects the thermal shift.
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
    
    # Setup Wavelengths (User Specification) - COMMENTED OUT TO RESTORE BASELINE
    # print("  Setting Wavelengths: 0.48, 0.55, 0.65")
    # waves = TheSystem.SystemData.Wavelengths
    # # Ensure 3 wavelengths
    # while waves.NumberOfWavelengths < 3:
    #     waves.AddWavelength(0.55, 1.0)
    # while waves.NumberOfWavelengths > 3:
    #     waves.RemoveWavelength(waves.NumberOfWavelengths)
        
    # w1 = waves.GetWavelength(1)
    # w1.Wavelength = 0.480
    # w1.Weight = 0.80
    
    # w2 = waves.GetWavelength(2)
    # w2.Wavelength = 0.550
    # w2.Weight = 1.00
    
    # w3 = waves.GetWavelength(3)
    # w3.Wavelength = 0.650
    # w3.Weight = 0.80
    
    # Set Air TCE
    LDE = TheSystem.LDE
    for i in range(1, LDE.NumberOfSurfaces):
        s = LDE.GetSurfaceAt(i)
        if s.Material.upper() == "" or s.Material.upper() == "AIR":
            s.TCE = 23.0

def get_spot_rms_from_analysis(TheSystem, ZOSAPI):
    """
    Run a Standard Spot Analysis and retrieve RMS Radius
    """
    # Open Analysis
    spot = TheSystem.Analyses.New_Analysis(ZOSAPI.Analysis.AnalysisIDM.StandardSpot)
    
    # Settings
    settings = spot.GetSettings()
    # settings.Wavelength.SetWavelengthNumber(0) # All
    # settings.Field.SetFieldNumber(0) # All
    
    # Run
    spot.ApplyAndWaitForCompletion()
    
    # Get Results
    results = spot.GetResults()
    
    # The result string usually contains the summary
    # Or we can look at the header data. 
    # For Spot Diagram, specific values are often in the text report or data grid.
    # Let's try to parse the header or use specific property if available.
    
    # Note: Accessing specific scalar results from analyses can be tricky in ZOS-API 
    # without parsing the text output.
    # However, 'StandardSpot' usually exposes summary data in the results.
    
    # Let's try reading the text file output
    report_file = os.path.join(TheSystem.TheApplication.SamplesDir, "temp_spot_report.txt")
    if os.path.exists(report_file):
        try: os.remove(report_file)
        except: pass
        
    results.GetTextFile(report_file)
    
    rms_val = -1.0
    
    if os.path.exists(report_file):
        # DEBUG: Print first few lines
        # print(f"DEBUG: Reading {report_file}")
        
        try:
            # Try UTF-16 first (Zemax default)
            with open(report_file, 'r', encoding='utf-16') as f:
                content = f.read()
        except:
            # Fallback to default/utf-8/latin-1
            with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
        # Look for "RMS radius    :"
        # print(f"DEBUG CONTENT LEN: {len(content)}")
        # print(content[:500]) # DEBUG
        
        for line in content.split('\n'):
            # Flexible check for RMS
            if "RMS" in line:
                # print(f"DEBUG LINE: {line.strip()}")
                # Format: "RMS radius    :  5.533 microns"
                if ":" in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        try:
                            val_str = parts[1].strip().split(' ')[0]
                            rms_val = float(val_str)
                            break
                        except: pass
        os.remove(report_file)
    else:
        print("DEBUG: Report file not generated!")
        
    spot.Close()
    return rms_val

def main():
    print("=" * 60)
    print("Task: Thermal Analysis via Spot Diagram Analysis")
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
        
        # 1. Setup
        setup_environment(TheSystem)
        
        # 2. Setup MCE
        MCE = TheSystem.MCE
        temps = [20, 50, 80]
        
        while MCE.NumberOfConfigurations < len(temps):
            MCE.AddConfiguration(True)
            
        op = MCE.GetOperandAt(1)
        op.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.TEMP)
        
        for i, t in enumerate(temps):
            op.GetOperandCell(i + 1).DoubleValue = float(t)
            
        # 3. Run Sweep using Analysis
        print("\nRunning Sweep...")
        for i, t in enumerate(temps):
            config = i + 1
            MCE.SetCurrentConfiguration(config)
            
            # CRITICAL: Wait for system to update?
            # TheSystem.Tools.RemoveAllVariables() # Triggers update?
            
            rms = get_spot_rms_from_analysis(TheSystem, ZOSAPI)
            print(f"  T={t}C (Config {config}): RMS Spot = {rms:.4f} microns")
            
    else:
        print(f"ERROR: Lens file not found at {lens_file}")

    zos.close()

if __name__ == "__main__":
    main()

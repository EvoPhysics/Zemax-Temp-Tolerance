"""
01_connect_zos.py - Zemax OpticStudio ZOS-API Connection Test

Task B: Hello World (Connectivity)
- Initialize ZOS-API connection
- Get Application instance
- Get Primary System
- Print Zemax version and current lens file name
"""

import clr
import os
import sys
import winreg


class PythonStandaloneApplication:
    """Zemax OpticStudio ZOS-API Standalone Application Connection"""
    
    def __init__(self):
        self.TheConnection = None
        self.TheApplication = None
        self.TheSystem = None
        
        # Step 1: Locate ZOSAPI_NetHelper.dll from Windows Registry
        try:
            aKey = winreg.OpenKey(
                winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER),
                r"Software\Zemax",
                0,
                winreg.KEY_READ
            )
            zemaxData = winreg.QueryValueEx(aKey, 'ZemaxRoot')
            winreg.CloseKey(aKey)
        except FileNotFoundError:
            raise Exception(
                "Zemax registry key not found. "
                "Please ensure Zemax OpticStudio is installed."
            )
        
        self.zemaxDir = zemaxData[0]
        netHelperPath = os.path.join(self.zemaxDir, r'ZOS-API\Libraries\ZOSAPI_NetHelper.dll')
        
        if not os.path.exists(netHelperPath):
            raise Exception(f"ZOSAPI_NetHelper.dll not found at: {netHelperPath}")
        
        # Step 2: Add NetHelper reference and initialize
        clr.AddReference(netHelperPath)
        import ZOSAPI_NetHelper
        
        isInitialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
        
        if not isInitialized:
            raise Exception(
                "Unable to initialize Zemax OpticStudio. "
                "Check if OpticStudio is properly installed."
            )
        
        # Step 3: Get Zemax directory and add API references
        zemaxDirectory = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
        
        zosapiPath = os.path.join(zemaxDirectory, "ZOSAPI.dll")
        zosapiInterfacesPath = os.path.join(zemaxDirectory, "ZOSAPI_Interfaces.dll")
        
        if not os.path.exists(zosapiPath):
            raise Exception(f"ZOSAPI.dll not found at: {zosapiPath}")
        
        clr.AddReference(zosapiPath)
        clr.AddReference(zosapiInterfacesPath)
        
        # Step 4: Import ZOSAPI namespace
        import ZOSAPI
        self.ZOSAPI = ZOSAPI
        
        # Step 5: Create connection
        self.TheConnection = ZOSAPI.ZOSAPI_Connection()
        
        if self.TheConnection is None:
            raise Exception("Unable to initialize .NET connection to ZOSAPI")
        
        # Step 6: Create new application instance (Standalone mode)
        print("Connecting to Zemax OpticStudio (Standalone mode)...")
        self.TheApplication = self.TheConnection.CreateNewApplication()
        
        if self.TheApplication is None:
            raise Exception(
                "Unable to acquire ZOSAPI application. "
                "Ensure OpticStudio is not already running in exclusive mode."
            )
        
        # Step 7: Validate license
        if not self.TheApplication.IsValidLicenseForAPI:
            raise Exception(
                "License is not valid for ZOSAPI use. "
                "API feature requires Professional or Premium edition."
            )
        
        # Step 8: Get Primary System
        self.TheSystem = self.TheApplication.PrimarySystem
        
        if self.TheSystem is None:
            raise Exception("Unable to acquire Primary system")
        
        print("Successfully connected to Zemax OpticStudio!")
    
    def get_version(self):
        """Get Zemax OpticStudio version string"""
        major = self.TheApplication.ZOSMajorVersion
        minor = self.TheApplication.ZOSMinorVersion
        sp = self.TheApplication.ZOSSPVersion
        return f"{major}.{minor}.{sp}"
    
    def get_version_full(self):
        """Get full Zemax OpticStudio version code"""
        return self.TheApplication.OpticStudioVersion
    
    def get_license_status(self):
        """Get license edition type"""
        return str(self.TheApplication.LicenseStatus)
    
    def get_lens_filename(self):
        """Get current lens file name"""
        name = self.TheSystem.SystemName
        return name if name else "(Untitled - No file loaded)"
    
    def get_lens_filepath(self):
        """Get full path to current lens file"""
        path = self.TheSystem.SystemFile
        return path if path else "(Not saved)"
    
    def get_samples_dir(self):
        """Get path to Zemax samples directory"""
        return self.TheApplication.SamplesDir
    
    def load_sample_file(self, relative_path):
        """Load a sample file from Zemax samples directory"""
        full_path = os.path.join(self.get_samples_dir(), relative_path)
        if os.path.exists(full_path):
            self.TheSystem.LoadFile(full_path, False)
            return True
        return False
    
    def close(self):
        """Clean up and close connection"""
        if self.TheApplication is not None:
            print("Closing Zemax OpticStudio connection...")
            self.TheApplication.CloseApplication()
            self.TheApplication = None
            self.TheConnection = None
            self.TheSystem = None
            print("Connection closed.")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


def main():
    """Main function to demonstrate ZOS-API connectivity"""
    
    print("=" * 60)
    print("Task B: Hello World (Connectivity)")
    print("=" * 60)
    print()
    
    zos = None
    try:
        # Initialize connection
        zos = PythonStandaloneApplication()
        
        print()
        print("-" * 60)
        print("CONNECTION INFO")
        print("-" * 60)
        
        # Get and print Zemax version
        version = zos.get_version()
        version_code = zos.get_version_full()
        license_status = zos.get_license_status()
        print(f"Zemax OpticStudio Version: {version} (build {version_code})")
        print(f"License Edition: {license_status}")
        
        # Get and print current lens file
        lens_name = zos.get_lens_filename()
        lens_path = zos.get_lens_filepath()
        print(f"Current Lens File: {lens_name}")
        print(f"Full Path: {lens_path}")
        
        # Try loading a sample file to demonstrate functionality
        print()
        print("-" * 60)
        print("LOADING SAMPLE FILE")
        print("-" * 60)
        
        sample_file = r"Sequential\Objectives\Cooke 40 degree field.zmx"
        print(f"Loading sample: {sample_file}")
        
        if zos.load_sample_file(sample_file):
            print(f"Loaded successfully!")
            print(f"Current Lens File: {zos.get_lens_filename()}")
            print(f"Full Path: {zos.get_lens_filepath()}")
        else:
            print(f"Sample file not found at expected location.")
            print(f"Samples directory: {zos.get_samples_dir()}")
        
        print()
        print("=" * 60)
        print("SUCCESS: ZOS-API connection test completed!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Connection failed!")
        print("=" * 60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Troubleshooting tips:")
        print("1. Ensure Zemax OpticStudio is installed")
        print("2. Check if you have a valid API license (Professional/Premium)")
        print("3. If seeing TargetInvocationException, verify .NET library paths")
        print("4. Try running as Administrator if registry access fails")
        sys.exit(1)
    
    finally:
        # Clean up
        if zos is not None:
            zos.close()


if __name__ == "__main__":
    main()

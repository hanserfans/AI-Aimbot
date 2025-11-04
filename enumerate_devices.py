#!/usr/bin/env python3
"""
Comprehensive Device Enumeration Script
Find G-Hub and Logitech device interfaces
"""

import sys
import os
import ctypes
import subprocess
import winreg
from ctypes import windll, wintypes
import win32api
import win32con

def is_admin():
    """Check if running with administrator privileges"""
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False

def enumerate_system_devices():
    """Enumerate all system devices using setupapi"""
    print("=== Enumerating System Devices ===")
    
    try:
        # Use PowerShell to get device information
        cmd = '''
        Get-WmiObject -Class Win32_PnPEntity | Where-Object {
            $_.Name -like "*Logitech*" -or 
            $_.Name -like "*G-Hub*" -or 
            $_.Name -like "*GHUB*" -or
            $_.DeviceID -like "*HID*" -or
            $_.Service -like "*LGHUB*"
        } | Select-Object Name, DeviceID, Service, Status | Format-Table -AutoSize
        '''
        
        result = subprocess.run(['powershell', '-Command', cmd], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout:
            print("Found Logitech/G-Hub related devices:")
            print(result.stdout)
        else:
            print("No Logitech/G-Hub devices found via WMI")
            
    except Exception as e:
        print(f"Error enumerating devices: {e}")

def check_registry_devices():
    """Check registry for device information"""
    print("\n=== Checking Registry for Device Information ===")
    
    registry_paths = [
        r"SYSTEM\CurrentControlSet\Enum\ROOT\SYSTEM",
        r"SYSTEM\CurrentControlSet\Services\LGHUB",
        r"SYSTEM\CurrentControlSet\Services\LGHUBUpdaterService",
        r"SOFTWARE\Logitech\Gaming Software",
        r"SOFTWARE\Logitech\LogiHub"
    ]
    
    for path in registry_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            print(f"\n✅ Found registry key: {path}")
            
            # Enumerate subkeys
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    print(f"  Subkey: {subkey_name}")
                    i += 1
                except OSError:
                    break
                    
            winreg.CloseKey(key)
            
        except FileNotFoundError:
            print(f"❌ Registry key not found: {path}")
        except Exception as e:
            print(f"❌ Error accessing registry key {path}: {e}")

def check_running_processes():
    """Check for running G-Hub processes"""
    print("\n=== Checking Running Processes ===")
    
    try:
        cmd = '''
        Get-Process | Where-Object {
            $_.ProcessName -like "*lghub*" -or 
            $_.ProcessName -like "*logitech*" -or
            $_.ProcessName -like "*ghub*"
        } | Select-Object ProcessName, Id, Path | Format-Table -AutoSize
        '''
        
        result = subprocess.run(['powershell', '-Command', cmd], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            print("Found G-Hub related processes:")
            print(result.stdout)
        else:
            print("No G-Hub processes found")
            
    except Exception as e:
        print(f"Error checking processes: {e}")

def check_services():
    """Check for G-Hub services"""
    print("\n=== Checking Services ===")
    
    try:
        cmd = '''
        Get-Service | Where-Object {
            $_.Name -like "*lghub*" -or 
            $_.Name -like "*logitech*"
        } | Select-Object Name, Status, StartType | Format-Table -AutoSize
        '''
        
        result = subprocess.run(['powershell', '-Command', cmd], 
                              capture_output=True, text=True, shell=True)
        
        if result.stdout.strip():
            print("Found G-Hub related services:")
            print(result.stdout)
        else:
            print("No G-Hub services found")
            
    except Exception as e:
        print(f"Error checking services: {e}")

def test_original_ginput():
    """Test if original g-input works"""
    print("\n=== Testing Original g-input ===")
    
    try:
        # Add g-input to path
        g_input_path = os.path.join(os.path.dirname(__file__), 'mouse_driver', 'g-input-main', 'g-input-main')
        if os.path.exists(g_input_path):
            sys.path.insert(0, g_input_path)
            
            # Try to import and test
            import mouse
            print("✅ Successfully imported original g-input mouse module")
            
            # Test mouse_open
            if mouse.mouse_open():
                print("✅ Original g-input mouse_open() succeeded!")
                mouse.mouse_close()
                return True
            else:
                print("❌ Original g-input mouse_open() failed")
                return False
        else:
            print("❌ g-input directory not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing original g-input: {e}")
        return False

def enumerate_device_interfaces():
    """Enumerate device interfaces using SetupAPI"""
    print("\n=== Enumerating Device Interfaces ===")
    
    # Common device interface GUIDs
    guids_to_test = [
        '{1abc05c0-c378-41b9-9cef-df1aba82b015}',  # Original g-input
        '{1bc4b5a5-8d52-4136-9f9b-2c7cd1a1e6e6}',  # Alternative
        '{4d1e55b2-f16f-11cf-88cb-001111000030}',  # HID
        '{745a17a0-74d3-11d0-b6fe-00a0c90f57da}',  # Keyboard
        '{378de44c-56ef-11d1-bc8c-00a0c91405dd}',  # Disk
    ]
    
    for guid in guids_to_test:
        print(f"\nTesting GUID: {guid}")
        for i in range(10):
            device_path = f'\\??\\ROOT#SYSTEM#000{i}#{guid}'
            
            try:
                handle = windll.kernel32.CreateFileW(
                    device_path,
                    0x80000000,  # GENERIC_READ
                    1,           # FILE_SHARE_READ
                    None,
                    3,           # OPEN_EXISTING
                    0,
                    None
                )
                
                if handle != -1:
                    print(f"✅ Found accessible device: {device_path}")
                    windll.kernel32.CloseHandle(handle)
                else:
                    error = windll.kernel32.GetLastError()
                    if error != 2:  # Don't spam "file not found" errors
                        print(f"❌ Device {device_path} - Error: {error}")
                        
            except Exception as e:
                print(f"❌ Exception testing {device_path}: {e}")

def main():
    print("G-Hub Device Enumeration and Diagnosis")
    print("=" * 60)
    print(f"Administrator privileges: {'Yes' if is_admin() else 'No'}")
    
    if not is_admin():
        print("⚠️  Warning: Some operations may require administrator privileges")
    
    # Run all diagnostic functions
    enumerate_system_devices()
    check_registry_devices()
    check_running_processes()
    check_services()
    enumerate_device_interfaces()
    test_original_ginput()
    
    print("\n" + "=" * 60)
    print("Diagnosis complete. Check the output above for any working device paths.")
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()
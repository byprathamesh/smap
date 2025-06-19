# 🔧 Reflex Frontend Troubleshooting Guide

## ✅ **SOLUTION SUMMARY**
The Reflex frontend issue has been **SUCCESSFULLY RESOLVED**! The app is now running at **http://localhost:3000**.

### Key Fixes Applied:
1. **Correct Package Structure**: Created proper `surveillance/surveillance.py` package structure
2. **Fixed Reflex Syntax**: Replaced Python boolean expressions with Reflex-compatible syntax
3. **Updated Config**: Set correct `app_name="surveillance"` in `rxconfig.py`
4. **Dependency Installation**: Ensured all Node.js and Python dependencies were installed

---

## 🚀 **QUICK START**

### **Method 1: Reflex Only (Frontend)**
```bash
cd surveillance_system
reflex run
```
✅ **Result**: Reflex frontend accessible at http://localhost:3000

### **Method 2: Complete System (Frontend + Backend)**
```bash
cd surveillance_system
python main_reflex.py
```
✅ **Result**: Full surveillance system with FastAPI backend (port 8000) + Reflex frontend (port 3000)

---

## 🔍 **COMMON ISSUES & SOLUTIONS**

### **Issue 1: "No module named 'surveillance.surveillance'"**
**Symptoms**: ModuleNotFoundError during Reflex startup
**Solution**:
```bash
# Ensure correct directory structure:
surveillance_system/
├── rxconfig.py (app_name="surveillance")
├── surveillance/
│   ├── __init__.py
│   └── surveillance.py (main Reflex app)
```

### **Issue 2: "Cannot convert Var to bool"**
**Symptoms**: VarTypeError during compilation
**Solution**: Replace Python boolean expressions with Reflex syntax:
```python
# ❌ Wrong:
color_scheme="green" if SurveillanceState.system_active else "gray"
disabled=not SurveillanceState.system_active

# ✅ Correct:
color_scheme=rx.cond(SurveillanceState.system_active, "green", "gray")
disabled=~SurveillanceState.system_active
```

### **Issue 3: "Invalid var passed for prop"**
**Symptoms**: TypeError about invalid property values
**Solution**: Use only valid Reflex property values:
```python
# ❌ Wrong:
justify="space-around"

# ✅ Correct:
justify="between"  # Valid options: "start", "center", "end", "between"
```

### **Issue 4: Port 3000 Already in Use**
**Symptoms**: Address already in use error
**Solution**:
```bash
# Find and kill process using port 3000
netstat -ano | findstr :3000
taskkill /PID [PID_NUMBER] /F

# Or use different port (not supported in current Reflex CLI)
```

### **Issue 5: Node.js/npm Not Found**
**Symptoms**: Node.js or npm command not recognized
**Solution**:
1. Install Node.js from https://nodejs.org/ (version 18.18.0+)
2. Restart terminal after installation
3. Verify: `node --version` and `npm --version`

### **Issue 6: Tailwind Deprecation Warnings**
**Symptoms**: Warning about inferring tailwind usage
**Solution**: Already fixed in `rxconfig.py`:
```python
config = rx.Config(
    app_name="surveillance",
    plugins=[rx.plugins.TailwindV3Plugin()],
)
```

---

## 🔧 **DIAGNOSTIC COMMANDS**

### **Check System Requirements**
```bash
# Python version (should be 3.10 or 3.11)
python --version

# Node.js version (should be 18.18.0+)
node --version

# npm version
npm --version

# Reflex version
pip show reflex
```

### **Check Reflex App Status**
```bash
# Test if app loads without errors
python -c "from surveillance.surveillance import app; print('✅ Reflex app loads successfully!')"

# Check if ports are in use
netstat -an | findstr :3000
netstat -an | findstr :8000

# Check running processes
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" -or $_.ProcessName -like "*reflex*"}
```

### **Test Frontend Access**
```bash
# Test if frontend is accessible
Invoke-WebRequest -Uri "http://localhost:3000" -Method Head

# Should return: StatusCode 200 OK
```

---

## 🛠 **STEP-BY-STEP RESET PROCEDURE**

If you encounter persistent issues, follow this complete reset:

### **1. Stop All Processes**
```bash
# Kill any existing Reflex/Node processes
Get-Process | Where-Object {$_.ProcessName -like "*reflex*"} | Stop-Process -Force
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force
```

### **2. Clean Installation**
```bash
# Reinstall Reflex (if needed)
pip uninstall reflex -y
pip install reflex

# Clear any cached frontend files
Remove-Item -Recurse -Force .web -ErrorAction SilentlyContinue
```

### **3. Verify Structure**
```bash
# Ensure correct file structure
surveillance_system/
├── rxconfig.py ✅
├── surveillance/
│   ├── __init__.py ✅
│   └── surveillance.py ✅
```

### **4. Fresh Start**
```bash
cd surveillance_system
reflex run --loglevel debug
```

---

## 📋 **TROUBLESHOOTING CHECKLIST**

- [ ] Python 3.10 or 3.11 installed
- [ ] Node.js 18.18.0+ installed  
- [ ] Reflex package installed (`pip show reflex`)
- [ ] Correct directory structure (`surveillance/surveillance.py`)
- [ ] Config file points to correct app (`app_name="surveillance"`)
- [ ] No Python boolean expressions in Reflex components
- [ ] Valid Reflex property values used
- [ ] Port 3000 available
- [ ] Can access http://localhost:3000 (returns 200 OK)

---

## 🎯 **VERIFICATION STEPS**

### **1. Confirm Reflex is Running**
```bash
# Should show listening ports
netstat -an | findstr :3000
```

### **2. Test Frontend Access**
Open browser and navigate to: **http://localhost:3000**

You should see:
- 🔍 **WatchHer Surveillance System** header
- **Advanced AI-Powered Security Monitoring** subtitle  
- **Source selection** (webcam/video_file)
- **Control buttons** (Start Webcam, Start Video, Stop Analysis)
- **Video feed area** with placeholder
- **Analytics panel** (Risk Score, FPS, Detections)
- **Activity Log** section

### **3. Expected Behavior**
- ✅ Page loads without errors
- ✅ UI components render properly
- ✅ Buttons are interactive (though backend functions require FastAPI backend)
- ✅ Console shows no JavaScript errors

---

## 📞 **SUPPORT INFORMATION**

**Successfully Tested Configuration:**
- **OS**: Windows 10.0.26100
- **Python**: 3.11.0
- **Node.js**: v22.15.0
- **npm**: 10.9.2  
- **Reflex**: 0.7.14

**Working URLs:**
- **Frontend**: http://localhost:3000 ✅
- **Backend** (when running): http://localhost:8000

**Status**: ✅ **FULLY FUNCTIONAL** - Reflex frontend successfully running and accessible.

---

*Last Updated: [Current Date]*
*Issue Resolution: COMPLETE ✅* 
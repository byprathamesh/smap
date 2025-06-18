# 🪟 Windows Command Prompt (cmd.exe) Setup Guide

## ✅ Virtual Environment Successfully Created!

Your virtual environment is now properly set up at:
```
C:\Users\prath\smap-1\surveillance_system\venv\
```

---

## 🔧 STEP-BY-STEP INSTRUCTIONS FOR CMD.EXE

### **1. Open Windows Command Prompt (cmd.exe)**
- Press `Win + R`, type `cmd`, press Enter
- OR: Search "Command Prompt" in Start Menu

### **2. Navigate to Project Directory**
```cmd
cd /d C:\Users\prath\smap-1\surveillance_system
```

### **3. Activate Virtual Environment (CORRECT CMD.EXE SYNTAX)**
```cmd
venv\Scripts\activate.bat
```

**✅ You should see `(venv)` appear at the beginning of your command prompt line.**

### **4. Install Dependencies**
```cmd
pip install -r requirements.txt
```

### **5. Start Python Interpreter**
```cmd
python
```

**✅ You should see the Python prompt: `>>>`**

### **6. Run Python Commands (INSIDE Python Interpreter)**
```python
# Test PyTorch and CUDA
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"CUDA device name: {torch.cuda.get_device_name()}")

# Test TensorFlow
import tensorflow as tf
print(f"TensorFlow version: {tf.__version__}")
print(f"TensorFlow GPU devices: {tf.config.list_physical_devices('GPU')}")

# Test YOLO
from ultralytics import YOLO
model = YOLO('yolov8n-pose.pt')
print(f"YOLO device: {model.device}")

# Exit Python interpreter
exit()
```

### **7. Run Your Surveillance System**
```cmd
python main.py
```

---

## ❌ COMMON MISTAKES TO AVOID

### **❌ WRONG: PowerShell syntax in cmd.exe**
```cmd
# DON'T USE THIS IN CMD.EXE:
.\venv\Scripts\activate     # This is PowerShell syntax!
```

### **✅ CORRECT: Batch file syntax for cmd.exe**
```cmd
# USE THIS IN CMD.EXE:
venv\Scripts\activate.bat   # This is cmd.exe syntax!
```

### **❌ WRONG: Running Python code directly in cmd.exe**
```cmd
# DON'T DO THIS IN CMD.EXE:
import torch               # This won't work!
print("Hello")            # This won't work!
```

### **✅ CORRECT: Running Python code inside Python interpreter**
```cmd
# STEP 1: Start Python interpreter in cmd.exe
python

# STEP 2: Now run Python code at the >>> prompt
>>> import torch
>>> print("Hello")
>>> exit()
```

---

## 🚀 QUICK REFERENCE

### **Complete Workflow for cmd.exe:**
```cmd
# 1. Open cmd.exe and navigate
cd /d C:\Users\prath\smap-1\surveillance_system

# 2. Activate virtual environment
venv\Scripts\activate.bat

# 3. You should see (venv) in your prompt
(venv) C:\Users\prath\smap-1\surveillance_system>

# 4. Run Python programs
python main.py
python quick_test.py
python test_features.py

# 5. For interactive Python
python
>>> import torch
>>> # ... your Python code here ...
>>> exit()

# 6. Deactivate when done
deactivate
```

---

## 🔍 TROUBLESHOOTING

### **If activation fails:**
```cmd
# Recreate virtual environment
rmdir /s venv
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### **If Python commands don't work:**
- Make sure you're in the Python interpreter (you see `>>>`)
- Make sure virtual environment is activated (you see `(venv)`)
- Check Python is installed: `python --version`

### **If CUDA/GPU not detected:**
- Install NVIDIA drivers
- Install CUDA toolkit
- Install cuDNN
- Reinstall PyTorch with CUDA support

---

## 💡 KEY DIFFERENCES: PowerShell vs cmd.exe

| Feature | PowerShell | cmd.exe |
|---------|------------|---------|
| Activation | `.\venv\Scripts\activate` | `venv\Scripts\activate.bat` |
| Path separator | `/` or `\` | `\` only |
| Script execution | `.ps1` files | `.bat` files |
| Case sensitivity | Less sensitive | Traditional Windows |

---

## ✅ SUCCESS INDICATORS

**Virtual environment activated correctly:**
```cmd
(venv) C:\Users\prath\smap-1\surveillance_system>
```

**Python interpreter running:**
```python
Python 3.11.x (main, ...) [MSC v.1916 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

**CUDA available (if you have GPU):**
```python
>>> import torch
>>> torch.cuda.is_available()
True
```

---

## 🎯 READY TO USE!

Once you see `(venv)` in your command prompt, you can run:
- `python main.py` - Start surveillance system
- `python quick_test.py` - Test risk scoring
- `python app.py` - Start web dashboard 
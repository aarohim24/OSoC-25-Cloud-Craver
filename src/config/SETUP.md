# Quick Setup Guide for Cloud Craver Configuration

## 🚀 Getting Started

Follow these steps to get the Dynaconf configuration system working:

### 1. Install Dependencies

Make sure you have the required packages installed. From the project root:

```bash
# Activate your virtual environment (if not already activated)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

If you get import errors, you might need to install specific packages:

```bash
pip install dynaconf pydantic toml pyyaml
```

### 2. Verify Installation

From the `src/config/` directory, run the simple test:

```bash
cd src/config/
python3 test_simple.py
```

This will check:
- ✅ Basic Python imports
- ✅ Dynaconf installation
- ✅ Configuration files exist
- ✅ Configuration loading works

### 3. Run the Demo

Once the test passes, run the main demo:

```bash
python3 demo.py
```

### 4. Create Local Settings (Optional)

For local development, copy the example settings:

```bash
cp local_settings.example.toml local_settings.toml
```

Then edit `local_settings.toml` with your preferences.

## 🐛 Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'dynaconf'"**
```bash
pip install dynaconf
```

**2. "ModuleNotFoundError: No module named 'config'"**
- Make sure you're running from the `src/config/` directory
- Check that `__init__.py` exists in the config directory

**3. Demo script runs but shows no output**
- The original demo script was corrupted - it's now fixed
- Try `python3 test_simple.py` first

**4. "No module named 'toml'"**
```bash
pip install toml
```

### Verification Steps

1. **Check Python version**: `python3 --version` (should be 3.7+)
2. **Check virtual environment**: Look for `(venv)` in your prompt
3. **Check working directory**: Should be in `src/config/`
4. **Check file permissions**: Make sure scripts are executable

## 📋 Quick Test Commands

```bash
# Test 1: Check if dynaconf works
python3 -c "from dynaconf import Dynaconf; print('Dynaconf works!')"

# Test 2: Check if config files exist
ls -la *.toml *.yaml

# Test 3: Load a simple TOML file
python3 -c "import toml; print(toml.load('settings.toml')['app']['name'])"

# Test 4: Run full diagnostic
python3 test_simple.py

# Test 5: Run demo
python3 demo.py
```

## ✅ Expected Output

When working correctly, `test_simple.py` should show:

```
🔍 Cloud Craver Configuration Debug
==================================================

📋 Testing: Basic imports
✅ Basic imports successful

📋 Testing: Dynaconf import
✅ Dynaconf import successful

📋 Testing: Configuration files
✅ settings.toml exists
✅ config.yaml exists
✅ base_config.toml exists

📋 Testing: Config file loading
✅ TOML file loaded successfully
   App name: Cloud Craver

📋 Testing: Dynaconf configuration
✅ Dynaconf configuration created
   App name: Cloud Craver

==================================================
📊 Test Results Summary:
   ✅ PASS: Basic imports
   ✅ PASS: Dynaconf import
   ✅ PASS: Configuration files
   ✅ PASS: Config file loading
   ✅ PASS: Dynaconf configuration

🎯 5/5 tests passed
🎉 All tests passed! Configuration system should be working.
```

## 🔧 Manual Configuration Test

If automated tests fail, try manual verification:

```python
# Create a simple Python script to test manually
from dynaconf import Dynaconf

# Load configuration
settings = Dynaconf(
    settings_files=["settings.toml"],
    envvar_prefix="CLOUDCRAVER"
)

print(f"App name: {settings.app.name}")
print(f"Default provider: {settings.cloud.default_provider}")
```

## 📞 Get Help

If you're still having issues:

1. Check the main [README.md](README.md) for detailed documentation
2. Verify all configuration files are in place
3. Make sure you're in a Python virtual environment
4. Check that all dependencies are installed

The configuration system provides robust error handling and should guide you through resolving any issues! 
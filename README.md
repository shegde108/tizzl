# tizzl

## Setup Instructions

### Virtual Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Fixing Import Issues

If you encounter import errors when running `python -m tizzl.run`, follow these steps:

#### Method 1: Development Installation
```bash
# Activate your virtual environment
source venv/bin/activate

# Install the project in development mode
cd tizzl
pip install -e .

# Add __init__.py files if missing
touch __init__.py

# Run the application
python run.py
```

  pip install chromadb
  pip install numpy
  pip install scikit-learn
  pip install sentence-transformers
  pip install fastapi uvicorn python-dotenv pydantic openai anthropic
#### Method 2: PYTHONPATH Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
cd tizzl
pip install -r requirements.txt

# Set PYTHONPATH to include the tizzl directory
export PYTHONPATH=/Users/shagun/Desktop/tizzl_v1/tizzl:$PYTHONPATH

# Run from the tizzl directory
python run.py
```

**Note:** Always run `python run.py` from within the `tizzl` directory, not `python -m tizzl.run` from the parent directory.

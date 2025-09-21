#!/usr/bin/env python3
"""
Run script for the MBL IMUViz FastAPI backend
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Add the src directory to Python path
    import sys
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    ) 
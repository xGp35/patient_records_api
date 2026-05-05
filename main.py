from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel

import json
app = FastAPI()

def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)
    
    return data
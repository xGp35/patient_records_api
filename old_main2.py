from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
from fastapi.responses import JSONResponse

class Patient(BaseModel):

    id: Annotated[str, Field(..., description= 'ID of the patient', examples=['P001'])]
    name: Annotated[str, Field(..., description = 'Name of the patient')]
    city: Annotated[str, Field(..., description= 'City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description = 'Age of the patient')]
    gender: Annotated[Literal['male','female','others'], Field(..., description= 'Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description = 'Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., gt=0, description = 'Weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5: 
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
        
class PatientUpdate(BaseModel):
    
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male','female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

import json
app = FastAPI()

def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)
    
    return data

def save_data(data):
    with open ('patients.json', 'w') as f:
        json.dump(data, f)

@app.get("/")
def hello():
    return {"message": "Patient Management System"}

@app.get('/about')
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get('/view')
def view():
    data = load_data()

    return data


@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(
    ..., description = "ID of the patient in the DB", examples = ["P001"] 
    )):
    # load all the patients
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code = 404, detail = "Patient not found")


@app.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description = 'Sort on the basis of height, weight or bmi'),
    order: str = Query (..., description = 'Sort in ascending or descending order')
):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code = 400, detail = f"Invalid field, select from {valid_fields}")
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code = 400, detail = f"Invalid field, select from 'asc', 'desc'")
    
    data = load_data()
    sort_order = True if order == 'desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)
    return sorted_data

@app.get('/patients')
def view_patients(
    sort_by: str | None = Query('bmi', description="Sort on the basis of height, weight or bmi"),
    order: str | None = Query("desc", description="Sort in ascending or descending order")
):
    data = load_data()

    patients = list(data.values())

    # Apply sort only if sort is provided
    if sort_by:
        valid_fields = ['height', 'weight', 'bmi']
        if sort_by not in valid_fields:
            raise HTTPException(status_code=400, detail=f"Invalid field selected, select from {valid_fields}")
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Order_by must be 'asc' or 'desc'")
    
    reverse_order = True if order == 'desc' else False

    patients = sorted(patients, key= lambda x: x.get(sort_by, 0), reverse=reverse_order)
    
    return patients

@app.post('/create')
def create_patient(patient: Patient):
    
    # load existing data
    data = load_data()
    # Check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists")
    # Add new patient to the database
    # To do that first - Convert pydantic object to dictionary (desrialization)
    data[patient.id] = patient.model_dump(exclude=['id']) # Because we store idas key and value is the rest

    # Save into json file
    save_data(data)

    return JSONResponse(status_code=201, content={'message': 'Patient created successfully'})

@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    
    # patient_id comes in url, the other data comes in body.
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code= 404, detail='Patient Not Found')
    
    existing_patient_info = data[patient_id]
    updted_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updted_patient_info.items():
        existing_patient_info[key] = value
    
    #existing_patient_info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id
    existing_patient_info = Patient(**existing_patient_info)

    # pydantic_objet -> dict
    existing_patient_info = existing_patient_info.model_dump(exclude='id')

    data[patient_id] = existing_patient_info

    # Save into json file
    save_data(data)

    return JSONResponse(
        status_code=200,
        content = {'message': "Patient updated Successfully"}
    )

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'patient deleted'})
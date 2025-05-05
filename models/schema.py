from pydantic import BaseModel, EmailStr

class QueryRequest(BaseModel):
    user_id: str
    question: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    age: int
    gender: str

class UserRegistration(BaseModel):
    name: str
    age: int
    gender: str
    email: str

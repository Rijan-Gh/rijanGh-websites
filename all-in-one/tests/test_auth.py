import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database_manager import db_manager
import json

# Test client
client = TestClient(app)

def test_register_customer():
    """Test customer registration"""
    response = client.post("/auth/register", json={
        "phone": "+919876543210",
        "password": "Test@123",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "customer"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["phone"] == "+919876543210"

def test_login():
    """Test user login"""
    # First register
    client.post("/auth/register", json={
        "phone": "+919876543211",
        "password": "Test@123",
        "role": "customer"
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "phone": "+919876543211",
        "password": "Test@123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_invalid_login():
    """Test invalid login credentials"""
    response = client.post("/auth/login", json={
        "phone": "+919876543212",
        "password": "WrongPassword"
    })
    
    assert response.status_code == 401

def test_refresh_token():
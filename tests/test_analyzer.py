"""
Test cases for the enhanced RepoAnalyzer library.

This module tests the improved false positive reduction capabilities
and validates the cross-detector integration in the enhanced version.
"""

import os
import sys
import unittest
import tempfile
import shutil
from typing import Dict, Any

# Import RepoAnalyzer
from repo_analyzer import RepoAnalyzer

class TestEnhancedRepoAnalyzer(unittest.TestCase):
    """Test cases for the enhanced RepoAnalyzer library."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test repositories
        self.test_dir = tempfile.mkdtemp()
        
        # Create test repositories
        self.python_repo = os.path.join(self.test_dir, "python_repo")
        self.node_repo = os.path.join(self.test_dir, "node_repo")
        self.mixed_repo = os.path.join(self.test_dir, "mixed_repo")
        self.minimal_repo = os.path.join(self.test_dir, "minimal_repo")
        
        os.makedirs(self.python_repo)
        os.makedirs(self.node_repo)
        os.makedirs(self.mixed_repo)
        os.makedirs(self.minimal_repo)
        
        # Create test files
        self._create_python_repo()
        self._create_node_repo()
        self._create_mixed_repo()
        self._create_minimal_repo()
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def _create_python_repo(self):
        """Create a Python repository structure with clear Flask and SQLAlchemy usage."""
        # Create directories
        os.makedirs(os.path.join(self.python_repo, "app"))
        os.makedirs(os.path.join(self.python_repo, "app", "models"))
        os.makedirs(os.path.join(self.python_repo, "app", "views"))
        os.makedirs(os.path.join(self.python_repo, "app", "templates"))
        os.makedirs(os.path.join(self.python_repo, "tests"))
        
        # Create main app file
        with open(os.path.join(self.python_repo, "app", "__init__.py"), "w") as f:
            f.write("""
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@db:5432/myapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app import views, models

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
""")
        
        # Create models
        with open(os.path.join(self.python_repo, "app", "models", "__init__.py"), "w") as f:
            f.write("""
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
""")
        
        # Create views
        with open(os.path.join(self.python_repo, "app", "views", "__init__.py"), "w") as f:
            f.write("""
from app import app, db
from app.models import User
from flask import render_template, jsonify, request

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201
""")
        
        # Create template
        with open(os.path.join(self.python_repo, "app", "templates", "index.html"), "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Flask App</title>
</head>
<body>
    <h1>Welcome to the Flask App</h1>
    <div id="users"></div>
    <script>
        fetch('/api/users')
            .then(response => response.json())
            .then(users => {
                const usersDiv = document.getElementById('users');
                users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.textContent = `${user.username} (${user.email})`;
                    usersDiv.appendChild(userDiv);
                });
            });
    </script>
</body>
</html>
""")
        
        # Create requirements.txt
        with open(os.path.join(self.python_repo, "requirements.txt"), "w") as f:
            f.write("""
flask==2.0.1
flask-sqlalchemy==2.5.1
psycopg2-binary==2.9.1
pytest==6.2.5
flask-testing==0.8.1
""")
        
        # Create a test
        with open(os.path.join(self.python_repo, "tests", "test_app.py"), "w") as f:
            f.write("""
import pytest
from app import app, db
from app.models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200

def test_get_users(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    assert response.json == []
""")
        
        # Create Dockerfile
        with open(os.path.join(self.python_repo, "Dockerfile"), "w") as f:
            f.write("""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app/__init__.py"]
""")
        
        # Create docker-compose.yml
        with open(os.path.join(self.python_repo, "docker-compose.yml"), "w") as f:
            f.write("""
version: '3'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
volumes:
  postgres_data:
""")
    
    def _create_node_repo(self):
        """Create a Node.js repository structure with clear Express and MongoDB usage."""
        # Create directories
        os.makedirs(os.path.join(self.node_repo, "src"))
        os.makedirs(os.path.join(self.node_repo, "src", "models"))
        os.makedirs(os.path.join(self.node_repo, "src", "routes"))
        os.makedirs(os.path.join(self.node_repo, "src", "controllers"))
        os.makedirs(os.path.join(self.node_repo, "public"))
        os.makedirs(os.path.join(self.node_repo, "test"))
        
        # Create main app file
        with open(os.path.join(self.node_repo, "src", "app.js"), "w") as f:
            f.write("""
const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
const userRoutes = require('./routes/users');

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
mongoose.connect('mongodb://mongo:27017/myapp', {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => console.log('Connected to MongoDB'))
.catch(err => console.error('MongoDB connection error:', err));

app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// Routes
app.use('/api/users', userRoutes);

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
""")
        
        # Create user model
        with open(os.path.join(self.node_repo, "src", "models", "user.js"), "w") as f:
            f.write("""
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    username: {
        type: String,
        required: true,
        unique: true
    },
    email: {
        type: String,
        required: true,
        unique: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('User', userSchema);
""")
        
        # Create user controller
        with open(os.path.join(self.node_repo, "src", "controllers", "userController.js"), "w") as f:
            f.write("""
const User = require('../models/user');

exports.getAllUsers = async (req, res) => {
    try {
        const users = await User.find();
        res.json(users);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
};

exports.createUser = async (req, res) => {
    const user = new User({
        username: req.body.username,
        email: req.body.email
    });

    try {
        const newUser = await user.save();
        res.status(201).json(newUser);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
};
""")
        
        # Create user routes
        with open(os.path.join(self.node_repo, "src", "routes", "users.js"), "w") as f:
            f.write("""
const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');

router.get('/', userController.getAllUsers);
router.post('/', userController.createUser);

module.exports = router;
""")
        
        # Create HTML file
        with open(os.path.join(self.node_repo, "public", "index.html"), "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Express App</title>
</head>
<body>
    <h1>Welcome to the Express App</h1>
    <div id="users"></div>
    <script>
        fetch('/api/users')
            .then(response => response.json())
            .then(users => {
                const usersDiv = document.getElementById('users');
                users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.textContent = `${user.username} (${user.email})`;
                    usersDiv.appendChild(userDiv);
                });
            });
    </script>
</body>
</html>
""")
        
        # Create package.json
        with open(os.path.join(self.node_repo, "package.json"), "w") as f:
            f.write("""
{
  "name": "express-app",
  "version": "1.0.0",
  "description": "Express application with MongoDB",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "mocha test/*.js"
  },
  "dependencies": {
    "express": "^4.17.1",
    "mongoose": "^6.0.12"
  },
  "devDependencies": {
    "mocha": "^9.1.3",
    "chai": "^4.3.4",
    "supertest": "^6.1.6",
    "nodemon": "^2.0.14"
  }
}
""")
        
        # Create a test
        with open(os.path.join(self.node_repo, "test", "app.test.js"), "w") as f:
            f.write("""
const chai = require('chai');
const expect = chai.expect;
const request = require('supertest');
const app = require('../src/app');
const mongoose = require('mongoose');

describe('API Tests', function() {
  before(function(done) {
    mongoose.connect('mongodb://localhost:27017/testdb', {
      useNewUrlParser: true,
      useUnifiedTopology: true
    }).then(() => done()).catch(err => done(err));
  });

  after(function(done) {
    mongoose.connection.close().then(() => done()).catch(err => done(err));
  });

  describe('GET /', function() {
    it('should return the index page', function(done) {
      request(app)
        .get('/')
        .expect(200)
        .end(done);
    });
  });

  describe('GET /api/users', function() {
    it('should return an array of users', function(done) {
      request(app)
        .get('/api/users')
        .expect(200)
        .expect('Content-Type', /json/)
        .expect(function(res) {
          expect(res.body).to.be.an('array');
        })
        .end(done);
    });
  });
});
""")
        
        # Create Dockerfile
        with open(os.path.join(self.node_repo, "Dockerfile"), "w") as f:
            f.write("""
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
""")
        
        # Create docker-compose.yml
        with open(os.path.join(self.node_repo, "docker-compose.yml"), "w") as f:
            f.write("""
version: '3'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    depends_on:
      - mongo
      
  mongo:
    image: mongo:4.4
    volumes:
      - mongo_data:/data/db
      
volumes:
  mongo_data:
""")
    
    def _create_mixed_repo(self):
        """Create a repository with mixed technology stack (React frontend, Python backend)."""
        # Create directories
        os.makedirs(os.path.join(self.mixed_repo, "backend"))
        os.makedirs(os.path.join(self.mixed_repo, "backend", "app"))
        os.makedirs(os.path.join(self.mixed_repo, "backend", "app", "api"))
        os.makedirs(os.path.join(self.mixed_repo, "backend", "app", "models"))
        os.makedirs(os.path.join(self.mixed_repo, "frontend"))
        os.makedirs(os.path.join(self.mixed_repo, "frontend", "src"))
        os.makedirs(os.path.join(self.mixed_repo, "frontend", "src", "components"))
        os.makedirs(os.path.join(self.mixed_repo, "frontend", "public"))
        
        # Create backend main.py
        with open(os.path.join(self.mixed_repo, "backend", "app", "main.py"), "w") as f:
            f.write("""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users
from app.models.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mixed Repo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}
""")
        
        # Create backend database.py
        with open(os.path.join(self.mixed_repo, "backend", "app", "models", "database.py"), "w") as f:
            f.write("""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""")
        
        # Create backend user model
        with open(os.path.join(self.mixed_repo, "backend", "app", "models", "user.py"), "w") as f:
            f.write("""
from sqlalchemy import Column, Integer, String
from app.models.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }
""")
        
        # Create backend users API
        with open(os.path.join(self.mixed_repo, "backend", "app", "api", "users.py"), "w") as f:
            f.write("""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/users", response_model=List[dict])
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [user.to_dict() for user in users]

@router.post("/users", response_model=dict)
def create_user(user_data: dict, db: Session = Depends(get_db)):
    db_user = User(username=user_data["username"], email=user_data["email"])
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.to_dict()
""")
        
        # Create backend requirements.txt
        with open(os.path.join(self.mixed_repo, "backend", "requirements.txt"), "w") as f:
            f.write("""
fastapi==0.70.0
uvicorn==0.15.0
sqlalchemy==1.4.27
pydantic==1.8.2
""")
        
        # Create frontend package.json
        with open(os.path.join(self.mixed_repo, "frontend", "package.json"), "w") as f:
            f.write("""
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "4.0.3",
    "axios": "^0.24.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
""")
        
        # Create frontend App.js
        with open(os.path.join(self.mixed_repo, "frontend", "src", "App.js"), "w") as f:
            f.write("""
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UserList from './components/UserList';

function App() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/users');
        setUsers(response.data);
        setLoading(false);
      } catch (err) {
        setError('Error fetching users');
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Mixed Repo App</h1>
      </header>
      <main>
        {loading ? (
          <p>Loading users...</p>
        ) : error ? (
          <p>{error}</p>
        ) : (
          <UserList users={users} />
        )}
      </main>
    </div>
  );
}

export default App;
""")
        
        # Create frontend UserList component
        with open(os.path.join(self.mixed_repo, "frontend", "src", "components", "UserList.js"), "w") as f:
            f.write("""
import React from 'react';

function UserList({ users }) {
  return (
    <div className="user-list">
      <h2>User List</h2>
      {users.length === 0 ? (
        <p>No users found</p>
      ) : (
        <ul>
          {users.map(user => (
            <li key={user.id}>
              <strong>{user.username}</strong> - {user.email}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default UserList;
""")
        
        # Create root docker-compose.yml
        with open(os.path.join(self.mixed_repo, "docker-compose.yml"), "w") as f:
            f.write("""
version: '3'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
""")
    
    def _create_minimal_repo(self):
        """Create a minimal repository with few files that shouldn't trigger false positives."""
        # Create directories
        os.makedirs(os.path.join(self.minimal_repo, "src"))
        
        # Create a simple Python script
        with open(os.path.join(self.minimal_repo, "src", "main.py"), "w") as f:
            f.write("""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
        
        # Create README.md
        with open(os.path.join(self.minimal_repo, "README.md"), "w") as f:
            f.write("""
# Minimal Repository

A minimal repository for testing.
""")
    
    def test_python_repo_detection(self):
        """Test detection of a Python repository with Flask and PostgreSQL."""
        analyzer = RepoAnalyzer(self.python_repo)
        tech_stack = analyzer.analyze()
        
        # Check language detection
        self.assertIn("Python", tech_stack["languages"])
        self.assertEqual(tech_stack["primary_technologies"]["languages"], "Python")
        
        # Check framework detection
        self.assertIn("Flask", tech_stack["frameworks"])
        self.assertIn("SQLAlchemy", tech_stack["frameworks"])
        
        # Check database detection
        self.assertIn("PostgreSQL", tech_stack["databases"])
        
        # Check build system and package manager detection
        self.assertIn("pip", tech_stack["package_managers"])
        
        # Check DevOps detection
        self.assertIn("Docker", tech_stack["devops"])
        
        # Check architecture detection (should be REST API or Layered Architecture)
        # Ensure it doesn't have false positives for architectures not present
        architecture_categories = list(tech_stack["architecture"].keys())
        self.assertTrue(
            "REST API" in architecture_categories or 
            "Layered Architecture" in architecture_categories
        )
        self.assertNotIn("Microservices", architecture_categories)
        self.assertNotIn("GraphQL API", architecture_categories)
        
        # Check testing detection
        self.assertIn("PyTest", tech_stack["testing"])
    
    def test_node_repo_detection(self):
        """Test detection of a Node.js repository with Express and MongoDB."""
        analyzer = RepoAnalyzer(self.node_repo)
        tech_stack = analyzer.analyze()
        
        # Check language detection
        self.assertIn("JavaScript", tech_stack["languages"])
        self.assertEqual(tech_stack["primary_technologies"]["languages"], "JavaScript")
        
        # Check framework detection
        self.assertIn("Express", tech_stack["frameworks"])
        
        # Check database detection
        self.assertIn("MongoDB", tech_stack["databases"])
        
        # Check build system and package manager detection
        self.assertIn("npm", tech_stack["package_managers"])
        
        # Check DevOps detection
        self.assertIn("Docker", tech_stack["devops"])
        
        # Check architecture detection (should be REST API)
        self.assertIn("REST API", tech_stack["architecture"])
        
        # Check testing detection
        self.assertIn("Mocha", tech_stack["testing"])
    
    def test_mixed_repo_detection(self):
        """Test detection of a mixed repository with React frontend and Python backend."""
        analyzer = RepoAnalyzer(self.mixed_repo)
        tech_stack = analyzer.analyze()
        
        # Check language detection (should detect both Python and JavaScript)
        self.assertIn("Python", tech_stack["languages"])
        self.assertIn("JavaScript", tech_stack["languages"])
        
        # Check framework detection (should detect both FastAPI and React)
        self.assertIn("FastAPI", tech_stack["frameworks"])
        self.assertIn("React", tech_stack["frameworks"])
        
        # Check database detection (should detect SQLite)
        self.assertIn("SQLite", tech_stack["databases"])
        
        # Check package managers (should detect both pip and npm)
        self.assertIn("pip", tech_stack["package_managers"])
        self.assertIn("npm", tech_stack["package_managers"])
        
        # Check DevOps detection
        self.assertIn("Docker", tech_stack["devops"])
    
    def test_minimal_repo_no_false_positives(self):
        """Test that a minimal repository doesn't trigger false positives."""
        analyzer = RepoAnalyzer(self.minimal_repo)
        tech_stack = analyzer.analyze()
        
        # Check language detection
        self.assertIn("Python", tech_stack["languages"])
        
        # There should be no frameworks detected
        self.assertEqual(len(tech_stack["frameworks"]), 0)
        
        # There should be no databases detected
        self.assertEqual(len(tech_stack["databases"]), 0)
        
        # There should be no build systems or package managers detected
        self.assertEqual(len(tech_stack["build_systems"]), 0)
        self.assertEqual(len(tech_stack["package_managers"]), 0)
        
        # There should be no DevOps tools detected
        self.assertEqual(len(tech_stack["devops"]), 0)
        
        # There should be no architecture patterns detected
        self.assertEqual(len(tech_stack["architecture"]), 0)
        
        # There should be no testing frameworks detected
        self.assertEqual(len(tech_stack["testing"]), 0)

if __name__ == "__main__":
    unittest.main()
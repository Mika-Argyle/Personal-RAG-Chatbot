# Personal Development Reference Commands

## 🎯 Quick Start Checklist

### New Development Session
- [ ] `cd ~/Development/Projects/Personal-RAG-Chatbot`
- [ ] `cd backend`
- [ ] `source venv/bin/activate`
- [ ] `git status`
- [ ] `git checkout main && git pull origin main`
- [ ] Start VS Code: `code .`

### Before Committing
- [ ] `git status`
- [ ] `git diff`
- [ ] Test the code works
- [ ] `git add .`
- [ ] `git commit -m "type: descriptive message `
    > `this commit will do this (in prent tense)"`
- [ ] `git push origin branch-name`

### End of Session
- [ ] Commit and push all work
- [ ] `deactivate` (exit venv)
- [ ] Document what you learned

---

## 🤖 RAG Chatbot Specific Commands

# Start development session
cd ~/Development/Projects/Personal-RAG-Chatbot/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Test Pinecone connection
curl http://localhost:8000/api/health/pinecone

---

## 🐍 Python Virtual Environment

### Setup & Activation
```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Deactivate
deactivate

# Check if in venv (should see):
(venv) mika@pop-os:~/Development/Projects/Personal-RAG-Chatbot/backend$

# See installed packages
pip list

# Install packages
pip install package-name

# Save dependencies
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

---

## 🔧 Git Workflow Commands

### Daily Workflow
```bash
# Check status
git status

# See what changed
git diff
git diff --name-only

# Start work session
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/branch-name

# Stage changes
git add .                    # All files
git add specific-file.py     # Specific file
git add *.py                # All Python files

# Commit with message
git commit -m "type: description"

# Push feature branch
git push origin feature/branch-name

# Switch branches
git checkout branch-name
git checkout main

# Delete branch (after merging)
git branch -d feature/branch-name
```

### Professional Commit Messages
```bash
# Format: type(scope): description
feat: add new feature
fix: resolve bug in authentication
docs: update API documentation
chore: update dependencies
refactor: reorganize code structure
test: add unit tests for user service
style: fix formatting and linting issues

# With body (for complex changes):
git commit -m "feat(auth): implement JWT authentication

- Add JWT token generation and validation
- Include refresh token functionality  
- Add middleware for protected routes
- Update user model with auth fields

Closes #25"
```

### Emergency Git Commands
```bash
# Undo last commit (keep changes)
git reset HEAD~1

# Undo changes to file
git checkout -- filename.py

# Save work temporarily
git stash
git stash pop

# View commit history
git log --oneline
git log --oneline --graph --all

# Check which branch you're on
git branch --show-current
```

---

## 🚀 FastAPI Development

### Running the Server
```bash
# Basic run
uvicorn app.main:app --reload

# With specific file structure
uvicorn app:app --reload        # if app.py in root
uvicorn backend.app.main:app    # if nested structure

# With custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing API Endpoints
```bash
# Using curl
curl http://localhost:8000
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Using httpie (if installed)
http GET localhost:8000/health
http POST localhost:8000/api/chat message="Hello"
```

### API Documentation
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

---

## 📊 Project Structure Commands

### Directory Navigation
```bash
# Go to project root
cd ~/Development/Projects/Personal-RAG-Chatbot

# Go to backend
cd backend

# Go back one level
cd ..

# Show current directory
pwd

# List files (detailed)
ls -la

# Create directory structure
mkdir -p app/services
mkdir -p app/models
mkdir -p app/routers

# Create files
touch app/__init__.py
touch app/services/__init__.py
```

### File Operations
```bash
# View file content
cat filename.py
head -20 filename.py    # First 20 lines
tail -20 filename.py    # Last 20 lines

# Edit in VS Code
code .                  # Open current directory
code filename.py        # Open specific file

# Copy files
cp source.py destination.py

# Move/rename files
mv old-name.py new-name.py
```

---

## 🔍 Debugging & Troubleshooting

### Python Issues
```bash
# Check Python version
python --version
python3 --version

# Check which Python you're using
which python
which python3

# Check installed packages
pip list
pip show package-name

# Check import paths
python -c "import sys; print('\n'.join(sys.path))"
```

### Environment Issues
```bash
# Check environment variables
env | grep PINECONE
echo $OPENAI_API_KEY

# Check if file exists
ls -la .env
cat .env
```

### Network/API Issues
```bash
# Test internet connection
ping google.com

# Test specific API endpoint
curl -I https://api.openai.com/v1/models

# Check running processes
ps aux | grep uvicorn
```

---

## 🔑 API Keys & Security

### Environment Variables
```bash
# Set temporary environment variable
export API_KEY="your-key-here"

# Check if variable is set
echo $API_KEY

# Load from .env file (in Python)
# Use python-dotenv package
```

### .env File Structure
```bash
# Example .env file content
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=portfolio-rag
PINECONE_ENVIRONMENT=us-east-1
REDIS_URL=redis://localhost:6379
```

---

## 📱 VS Code Shortcuts

### Essential Shortcuts
```
Ctrl+Shift+P        # Command palette
Ctrl+`              # Toggle terminal
Ctrl+Shift+G        # Source control
Ctrl+Shift+E        # Explorer
Ctrl+/              # Toggle comment
Ctrl+D              # Select next occurrence
Ctrl+Shift+L        # Select all occurrences
F2                  # Rename symbol
```

### Git in VS Code
```
Ctrl+Shift+G        # Open source control
Stage changes       # Click + next to files
Commit              # Type message, Ctrl+Enter
Push/Pull           # Click sync button
Create branch       # Command palette: "Git: Create Branch"
```

---

## 🐛 Common Issues & Solutions

### Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution 1: Check if __init__.py exists
touch app/__init__.py

# Solution 2: Run from correct directory
cd backend
uvicorn app.main:app --reload

# Solution 3: Add to Python path
PYTHONPATH=. uvicorn app.main:app --reload
```

### Git Authentication
```bash
# Problem: Authentication failed
# Solution: Use VS Code for Git operations
# Or set up SSH keys / personal access tokens

# Check current remote
git remote -v

# Update to SSH (if using SSH keys)
git remote set-url origin git@github.com:username/repo.git
```

### Package Installation Issues
```bash
# Problem: Package conflicts
# Solution: Use fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---


## 📚 Learning Resources

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Git**: https://git-scm.com/docs
- **Python**: https://docs.python.org/3/

### API Testing
- **Interactive Docs**: http://localhost:8000/docs
- **curl Examples**: See testing section above
- **Postman**: GUI tool for API testing

---

## 💡 Pro Tips

### Productivity Hacks
1. **Use aliases** in your shell config for long commands
2. **Keep this file open** in a second VS Code tab
3. **Update regularly** as you learn new commands
4. **Add project-specific notes** for complex setups

### Professional Practices
1. **Always work in feature branches**
2. **Write descriptive commit messages**
3. **Keep virtual environments clean**
4. **Document as you learn**
5. **Test before committing**

---

*This reference is a living document - update it as you learn new commands and workflows!*
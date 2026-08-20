# Two-Developer GitHub Collaboration Quickstart
## AI-Powered Adaptive Exam Learning Platform

A 1-page cheat sheet for the **Backend Lead** and **Frontend Developer** to work simultaneously with **zero Git conflicts**.

---

## 🛑 The 3 Golden Rules
1. **Directory Isolation:** Backend Developer **only** edits files in `backend/`. Frontend Developer **only** edits files in `frontend/`.
2. **Never commit directly to `main`:** Always create a short-lived branch for your active WBS task (`feat/be-...` or `feat/fe-...`).
3. **Always sync `main` before branching:** Run `git checkout main && git pull --rebase origin main` before starting any new task.

---

## 🛠️ Developer 1: Backend Track Cheat Sheet (FastAPI / Python)

### 1. Starting a New Backend Task
```powershell
# Make sure your local main is up to date
git checkout main
git pull --rebase origin main

# Create your isolated backend feature branch
git checkout -b feat/be-task-0.4-llm-gateway
```

### 2. Working & Testing
* Work **exclusively** inside `backend/`.
* Run your test suite to ensure 100% green tests:
```powershell
pytest backend/tests/test_health.py -v
```

### 3. Committing & Pushing to GitHub
```powershell
# Stage ONLY your backend files
git add backend/ .agents/state/

# Commit using the Task ID format
git commit -m "feat(api): [Task-0.4] implement multi-provider LLM gateway"

# Push to GitHub
git push -u origin feat/be-task-0.4-llm-gateway
```
*Open Pull Request on GitHub → Merge into `main` after CI passes.*

---

## 🎨 Developer 2: Frontend Track Cheat Sheet (React / TypeScript)

### 1. Starting a New Frontend Task
```powershell
# Make sure your local main is up to date
git checkout main
git pull --rebase origin main

# Create your isolated frontend feature branch
git checkout -b feat/fe-task-0.3-react-scaffold
```

### 2. Working & Testing
* Work **exclusively** inside `frontend/`.
* Run build & tests to verify type safety:
```powershell
cd frontend
npm run build
npm run test
```

### 3. Committing & Pushing to GitHub
```powershell
# Stage ONLY your frontend files
git add frontend/ .agents/state/

# Commit using the Task ID format
git commit -m "feat(ui): [Task-0.3] scaffold React Vite workspace and design system"

# Push to GitHub
git push -u origin feat/fe-task-0.3-react-scaffold
```
*Open Pull Request on GitHub → Merge into `main` after CI passes.*

---

## 🔄 How the Two Tracks Sync API Changes (Zero Blocking)

```text
Backend Developer (FastAPI)               Frontend Developer (React / TS)
--------------------------               -------------------------------
1. Designs Pydantic Schema               
2. Exports docs/contracts/openapi.json   
3. Merges backend PR to main             
                                         4. Pulls main (git pull --rebase)
                                         5. Runs: npm run typegen
                                            (Auto-generates TS types from openapi.json)
                                         6. Builds UI with MSW Mock Data
```

---

## 🆘 Quick Troubleshooting

| Situation | What to Run |
| :--- | :--- |
| **"I want to make sure my branch has my teammate's latest merged work"** | `git fetch origin main`<br/>`git rebase origin/main` |
| **"Git says I have uncommitted changes when trying to pull"** | `git stash`<br/>`git pull --rebase origin main`<br/>`git stash pop` |
| **"I accidentally edited a file in the other person's folder"** | `git checkout -- frontend/` (if you are backend)<br/>`git checkout -- backend/` (if you are frontend) |

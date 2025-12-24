# 🚀 Complete Setup Guide - PupilPrep Frontend

This guide will help you get the entire PupilPrep system running (Backend + Frontend).

## 📋 Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.8+
- **MongoDB** (running locally or Atlas)
- **API Keys**:
  - Gemini API Key
  - Pinecone API Key
  - YouTube API Keys

## 🎯 Quick Start (Both Backend & Frontend)

### Option 1: Automated Setup (Recommended)

```bash
# From project root
cd "c:\Users\omkar\Desktop\New folder\ai project\Pupil-prep-AI-Powered-Personalized-Learning-Platform"

# 1. Setup Backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# 2. Setup Frontend
cd frontend
npm install

# 3. Run both servers
# Terminal 1 - Backend
cd ..
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Option 2: Step-by-Step Setup

## 🔧 Backend Setup

### 1. Create Virtual Environment
```bash
cd "c:\Users\omkar\Desktop\New folder\ai project\Pupil-prep-AI-Powered-Personalized-Learning-Platform"
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Environment Variables
Your `.env` file should already have:
```env
MONGO_URI=mongodb+srv://python_AI:majar123@cluster0.mfempxz.mongodb.net/python_AI?retryWrites=true&w=majority
GEMINI_API_KEY=AIzaSyAS7NrWwIc1zYkNzKNYBUR0HIenyNrdVWA
TARGET_MONGO_URI=mongodb+srv://python_AI:majar123@cluster0.mfempxz.mongodb.net/python_AI?retryWrites=true&w=majority
DB_STRUCT_URI=mongodb+srv://python_AI:majar123@cluster0.mfempxz.mongodb.net/
YOUTUBE_API_KEY_1=AIzaSyB5fHV3YdqpX4qlqfOY50Seh_IEg444eVE
# ... more API keys
PINECONE_API_KEY=pcsk_5arBNU_KdDQbBfk866JuStk5DpDWszsQN56PG3UrrSPe7FUsTGLV24CKNwbqPLJJfkD93s
PINECONE_ENVIRONMENT=us-east-1
```

### 4. Start Backend Server
```bash
python main.py
```

✅ Backend should now be running on: **http://localhost:8080**

### 5. Test Backend API
```bash
curl http://localhost:8080/api/v1/ping
```
Expected response: `{"status": "ok"}`

## 💻 Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Dependencies
```bash
npm install
# or
yarn install
```

### 3. Verify Environment Variables
Check `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api
NEXT_PUBLIC_SOCKET_URL=http://localhost:8080
```

### 4. Start Development Server
```bash
npm run dev
# or
yarn dev
```

✅ Frontend should now be running on: **http://localhost:3000**

## 🌐 Access the Application

### Landing Page
```
http://localhost:3000
```

### Login Page
```
http://localhost:3000/login
```

### Teacher Dashboard
```
http://localhost:3000/teacher/dashboard
```

### Student Dashboard
```
http://localhost:3000/student/dashboard
```

## 🔐 Demo Accounts

### Teacher Account
```
Email: teacher@demo.com
Password: password123
```

### Student Account
```
Email: student@demo.com
Password: password123
```

## ✅ Verification Checklist

- [ ] Backend running on port 8080
- [ ] Frontend running on port 3000
- [ ] Can access landing page
- [ ] Can login as teacher
- [ ] Can login as student
- [ ] Teacher dashboard loads
- [ ] Student dashboard loads
- [ ] Content generation form works
- [ ] API calls successful

## 🎨 Key Features to Test

### Teacher Portal (PupilTeach)
1. **Login** → http://localhost:3000/login
2. **Dashboard** → View classes, sessions, stats
3. **Content Generation** → 
   - Go to "Content Generation"
   - Select a class
   - Enter topic (e.g., "Newton's Laws")
   - Select learning modes
   - Click "Generate Content"
   - Watch progress bar
4. **Assessments** → Create AI-powered assessments
5. **Classes** → Manage students and performance

### Student Portal (PupilLearn)
1. **Login** → http://localhost:3000/login
2. **Dashboard** → View daily tasks, streak, XP
3. **My Learning** → Access 10 learning modes
4. **Progress** → Track performance analytics
5. **Achievements** → View badges and rewards

## 🛠️ Troubleshooting

### Issue: Backend not starting
```bash
# Check if port 8080 is in use
netstat -ano | findstr :8080

# Kill the process if needed
taskkill /PID <PID> /F

# Restart backend
python main.py
```

### Issue: Frontend not starting
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

### Issue: API connection failed
1. Verify backend is running: `curl http://localhost:8080/api/v1/ping`
2. Check `.env.local` has correct API URL
3. Check browser console for CORS errors

### Issue: MongoDB connection failed
1. Verify MongoDB URI in `.env`
2. Check internet connection (if using Atlas)
3. Whitelist your IP in MongoDB Atlas

### Issue: Content generation fails
1. Check Gemini API key is valid
2. Check Pinecone API key is valid
3. View backend logs for errors

## 📊 Project Status

### ✅ Completed Features

**Backend**
- ✅ Multi-agent system (Content, Assessment, Remedy)
- ✅ 10 learning modes implementation
- ✅ RAG system with Pinecone
- ✅ Assessment generation
- ✅ MongoDB integration
- ✅ FastAPI REST APIs
- ✅ Job management system

**Frontend**
- ✅ Next.js 14 + TypeScript setup
- ✅ Authentication system
- ✅ Teacher dashboard
- ✅ Student dashboard
- ✅ Content generation interface
- ✅ API integration
- ✅ Real-time WebSocket support
- ✅ Responsive design (mobile, tablet, desktop)

### 🚧 In Progress
- [ ] All 10 learning modes UI components
- [ ] Assessment creation wizard
- [ ] Live class management
- [ ] Advanced analytics dashboards

### 📅 Planned Features
- [ ] Mobile PWA
- [ ] Offline mode
- [ ] Advanced gamification
- [ ] Video conferencing integration
- [ ] Parent portal

## 🔗 Important URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main web app |
| Backend API | http://localhost:8080/api | REST API |
| API Docs | http://localhost:8080/docs | Swagger UI |
| MongoDB | mongodb+srv://... | Database |

## 📚 Documentation

- **Frontend**: `/frontend/README.md`
- **Backend API**: `/docs/API_DOCUMENTATION.md`
- **System Overview**: `/docs/SYSTEM_OVERVIEW.md`
- **Developer Guide**: `/docs/DEVELOPER_ONBOARDING.md`

## 🎯 Next Steps

1. **Test Core Flows**:
   - Create a teacher account
   - Generate after-hour content
   - Create an assessment
   - View student dashboard

2. **Customize**:
   - Add your branding
   - Configure settings
   - Add custom learning modes

3. **Deploy**:
   - Backend: Railway, Render, or AWS
   - Frontend: Vercel or Netlify
   - Database: MongoDB Atlas

## 💡 Pro Tips

1. **Keep both terminals open** - Backend (Terminal 1) + Frontend (Terminal 2)
2. **Use browser DevTools** - Check Network tab for API calls
3. **Check logs** - Backend terminal shows all API requests
4. **Use demo accounts** - Pre-configured for testing
5. **Clear cache** - If you see stale data, clear browser cache

## 🆘 Need Help?

- Check logs in backend terminal
- Open browser DevTools console
- Review API documentation
- Check MongoDB connection
- Verify all environment variables

---

## 🎉 Success!

If you can:
- ✅ Login as teacher
- ✅ See dashboard
- ✅ Generate content (job completes)
- ✅ Login as student
- ✅ View learning tasks

**Congratulations! Your PupilPrep system is fully functional!** 🚀

---

**Last Updated**: December 25, 2025
**Version**: 1.0.0

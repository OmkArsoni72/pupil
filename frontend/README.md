# PupilPrep Frontend

Modern, responsive web application for PupilPrep AI-Powered Personalized Learning Platform.

## 🚀 Features

### Teacher Portal (PupilTeach)
- ✅ **Content Generation**: Generate multi-modal learning content in 10 different learning modes
- ✅ **Assessment Creation**: AI-powered assessment and quiz generation
- ✅ **Class Management**: Manage multiple classes and students
- ✅ **Real-time Analytics**: Live performance tracking during classes
- ✅ **Learning Gap Analysis**: Automated identification and remediation

### Student Portal (PupilLearn)
- ✅ **Personalized Learning**: 10 unique learning modes
- ✅ **Adaptive Remediation**: AI-driven gap filling
- ✅ **Progress Tracking**: Comprehensive performance analytics
- ✅ **Interactive Assessments**: Engaging quizzes and tests
- ✅ **Gamification**: Points, badges, and achievements

### Learning Modes
1. 📖 **Learn by Reading** - Structured notes with visuals
2. ✍️ **Learn by Writing** - Writing prompts & essays
3. 🎥 **Learn by Watching** - Curated YouTube videos
4. 🎮 **Learn by Playing** - Educational games
5. 🔬 **Learn by Doing** - Hands-on experiments
6. 🧮 **Learn by Solving** - Problem sets & practice
7. ❓ **Learn by Questioning** - Debate & Socratic method
8. 🎧 **Learn by Listening** - Audio content & podcasts
9. 📝 **Learn by Assessment** - Quizzes & tests

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (React)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **API Calls**: Axios + React Query
- **Real-time**: Socket.IO Client
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **Icons**: React Icons

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8080`

### Setup Steps

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
# or
yarn install
```

3. **Configure environment variables**
Create a `.env.local` file (already created):
```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api
NEXT_PUBLIC_SOCKET_URL=http://localhost:8080
```

4. **Run development server**
```bash
npm run dev
# or
yarn dev
```

5. **Open browser**
Navigate to [http://localhost:3000](http://localhost:3000)

## 🏃‍♂️ Running the Application

### Development Mode
```bash
npm run dev
```
Starts the development server with hot reload at `http://localhost:3000`

### Production Build
```bash
npm run build
npm start
```

### Linting
```bash
npm run lint
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Authentication pages
│   │   │   ├── login/         # Login page
│   │   │   └── register/      # Registration page
│   │   ├── teacher/           # Teacher portal
│   │   │   ├── dashboard/     # Teacher dashboard
│   │   │   ├── content/       # Content generation
│   │   │   ├── assessments/   # Assessment management
│   │   │   ├── classes/       # Class management
│   │   │   ├── timetable/     # Timetable view
│   │   │   └── reports/       # Analytics & reports
│   │   ├── student/           # Student portal
│   │   │   ├── dashboard/     # Student dashboard
│   │   │   ├── learn/         # Learning modes
│   │   │   ├── assessments/   # Take assessments
│   │   │   └── progress/      # Progress tracking
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Landing page
│   │   └── globals.css        # Global styles
│   ├── components/            # Reusable components
│   │   ├── ui/               # UI components
│   │   ├── dashboard/        # Dashboard widgets
│   │   ├── learning-modes/   # Learning mode components
│   │   └── common/           # Common components
│   ├── lib/                   # Utilities & configs
│   │   ├── api/              # API client
│   │   ├── socket.ts         # WebSocket client
│   │   └── utils.ts          # Helper functions
│   ├── store/                 # State management
│   │   └── authStore.ts      # Auth state
│   └── types/                 # TypeScript types
│       └── index.ts          # Type definitions
├── public/                    # Static assets
├── package.json              # Dependencies
├── tsconfig.json            # TypeScript config
├── tailwind.config.ts       # Tailwind config
└── next.config.js           # Next.js config
```

## 🔑 Authentication

### Demo Credentials
- **Teacher**: `teacher@demo.com` / `password123`
- **Student**: `student@demo.com` / `password123`

### User Roles
- `teacher` - Full teacher access
- `student` - Student learning portal
- `admin` - Administrative access
- `hod` - Head of Department
- `dean` - Dean access

## 🎨 UI/UX Features

### Responsive Design
- ✅ Mobile-first approach
- ✅ Tablet optimization (768px+)
- ✅ Desktop full experience (1024px+)
- ✅ Fluid layouts with TailwindCSS

### Accessibility
- ARIA labels and roles
- Keyboard navigation
- Screen reader support
- High contrast mode

### Performance
- Code splitting
- Lazy loading
- Image optimization
- API caching with React Query

## 🔌 API Integration

The frontend connects to the PupilPrep Backend API:

### Base URL
```
http://localhost:8080/api
```

### Main Endpoints Used
- `POST /v1/users/login` - User authentication
- `POST /v1/users/register` - User registration
- `POST /v1/contentGenerationForAHS` - After-hour content
- `POST /v1/contentGenerationForRemedies` - Remediation content
- `POST /v1/assessments/generate` - Assessment generation
- `GET /v1/jobs/{job_id}` - Job status tracking
- `GET /v1/teacher/classes` - Teacher classes
- `GET /v1/sessions` - Class sessions

See [Backend API Documentation](../docs/API_DOCUMENTATION.md) for full details.

## 🌐 WebSocket Events

Real-time features using Socket.IO:

### Events Emitted
- `join_class` - Join a class room
- `push_question` - Push question to students
- `submit_answer` - Submit student answer

### Events Listened
- `question_pushed` - New question pushed
- `student_answered` - Student submitted answer
- `session_started` - Session started
- `session_ended` - Session ended
- `job_progress` - Content generation progress

## 🚧 Development Roadmap

### Phase 1: Core Features (Current) ✅
- [x] Project setup
- [x] Authentication system
- [x] Teacher dashboard
- [x] Content generation interface
- [x] Basic API integration

### Phase 2: Advanced Features (Next)
- [ ] All 10 learning modes implementation
- [ ] Student portal complete
- [ ] Real-time class management
- [ ] Assessment creation & management
- [ ] Analytics dashboards

### Phase 3: Enhancement
- [ ] Mobile progressive web app (PWA)
- [ ] Offline mode support
- [ ] Advanced gamification
- [ ] Performance optimization
- [ ] Comprehensive testing

## 🐛 Troubleshooting

### Common Issues

**1. API Connection Failed**
```
Error: Network Error
```
**Solution**: Ensure backend is running on `http://localhost:8080`

**2. Authentication Issues**
```
Error: Unauthorized (401)
```
**Solution**: Clear browser localStorage and login again

**3. Build Errors**
```
Error: Module not found
```
**Solution**: Delete `node_modules` and `.next`, then reinstall:
```bash
rm -rf node_modules .next
npm install
```

**4. Port Already in Use**
```
Error: Port 3000 is already in use
```
**Solution**: Use a different port:
```bash
PORT=3001 npm run dev
```

## 📝 Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8080/api
NEXT_PUBLIC_SOCKET_URL=http://localhost:8080

# Optional
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for all new files
3. Follow TailwindCSS utility-first approach
4. Add proper types for API responses
5. Test on mobile, tablet, and desktop

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)

## 📄 License

Copyright © 2025 PupilPrep. All rights reserved.

---

**Built with ❤️ using Next.js & TypeScript**

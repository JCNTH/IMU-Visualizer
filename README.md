# MBL IMUViz - IMU Visualization & Inverse Kinematics

A modern web application for IMU (Inertial Measurement Unit) sensor visualization and inverse kinematics processing for biomechanics research.

## Architecture

This application has been converted from a Flask/vanilla JS application to a modern full-stack architecture:

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and shadcn/ui
- **Backend**: FastAPI with Python for high-performance API endpoints
- **Database**: Supabase (PostgreSQL) with Row Level Security
- **State Management**: Zustand for client-side state
- **Authentication**: Supabase Auth with JWT tokens
- **Styling**: Tailwind CSS with shadcn/ui components
- **3D Visualization**: Three.js for IMU sensor placement and visualization

## Features

- **🔐 User Authentication**: Secure login/signup with Supabase Auth
- **📊 Project Management**: Organize your IMU analysis projects
- **📡 Sensor Mapping**: Upload and parse sensor placement files
- **⚙️ Calibration Tasks**: Multiple calibration task management with sensor selection
- **🔄 Main Task Processing**: Process IMU data for inverse kinematics
- **📈 IK Parameters**: Configure sensor setup, filters, dimensions, and offset removal
- **🎯 3D Visualization**: Interactive 3D model with IMU placement visualization
- **🎬 Video Generation**: Generate MP4 videos from IK results using OpenSim models
- **💾 Data Export**: Download results as CSV files and visualization graphs
- **☁️ Cloud Storage**: Store and manage your data in Supabase
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

## Quick Start

> **📖 For detailed setup instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)**

### Prerequisites

- **Python 3.10+** and **Node.js 18+**
- **Supabase account** (free tier available)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd mbl_imuviz
```

### 2. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Run the SQL migration in `supabase/migrations/001_initial_schema.sql`
3. Get your project URL and API keys

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
cp env.example .env
# Edit .env with your Supabase credentials
python run.py
```

### 4. Frontend Setup

```bash
cd frontend
pnpm install
cp env.example .env.local
# Edit .env.local with your Supabase credentials
pnpm dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Environment Variables

### Backend (.env)
```bash
# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Database
DATABASE_URL=postgresql://postgres:password@db.your-project-ref.supabase.co:5432/postgres

# API Configuration
CORS_ORIGINS=http://localhost:3000
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### Frontend (.env.local)
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
mbl_imuviz/
├── backend/                    # FastAPI backend
│   ├── src/api/
│   │   ├── main.py            # Main FastAPI application
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic services
│   │   ├── database/          # Database models and config
│   │   └── utils/             # Utility functions
│   ├── pyproject.toml         # Python dependencies
│   └── run.py                 # Backend run script
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/       # React components
│   │   ├── lib/             # Utilities and API functions
│   │   ├── hooks/           # Custom React hooks
│   │   └── store/           # Zustand state management
│   └── package.json         # Node.js dependencies
├── supabase/
│   └── migrations/          # Database migrations
└── README.md               # This file
```

## Database Schema

The application uses the following main entities:

- **Users**: User accounts and profiles
- **Projects**: IMU analysis projects
- **Sensor Mappings**: Sensor ID to body position mappings
- **Calibration Tasks**: Calibration task configurations
- **Sensor Data**: Raw and processed sensor data
- **IK Processing**: Inverse kinematics processing jobs
- **Video Generations**: Video generation tasks

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Projects
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details

### IMU Processing
- `POST /api/upload_sensor_mapping` - Upload sensor mapping file
- `POST /api/upload_calibration` - Upload calibration files
- `POST /api/upload_main_task` - Upload main task files
- `POST /api/run_ik` - Run inverse kinematics processing
- `GET /api/download_csv` - Download IK results as CSV
- `GET /api/download_graphs_zip` - Download visualization graphs
- `GET /api/generate_video_stream` - Generate video with streaming progress

## Development

### Adding New Features

1. **Database**: Create migration in `supabase/migrations/`
2. **Backend**: Add models, services, and endpoints
3. **Frontend**: Create components and update state management
4. **Testing**: Add tests for new functionality

### Code Style

- **Backend**: Follow PEP 8 and use type hints
- **Frontend**: Use TypeScript strict mode and ESLint
- **Components**: Use shadcn/ui for consistent styling
- **Database**: Follow PostgreSQL best practices

## Migration from Original App

This application maintains 100% compatibility with the original Flask app:

- ✅ **Sensor mapping** upload and parsing
- ✅ **Calibration task** management
- ✅ **Main task** data processing
- ✅ **IK parameter** configuration
- ✅ **Inverse kinematics** processing
- ✅ **CSV and graph** downloads
- ✅ **Video generation** with streaming progress
- ✅ **3D visualization** (enhanced with modern Three.js)

**New Features Added:**
- 🔐 User authentication and project management
- ☁️ Cloud data storage and persistence
- 📱 Mobile-responsive design
- 🎨 Modern UI with shadcn/ui components
- 🚀 Improved performance and scalability

## Production Deployment

### Recommended Stack

- **Frontend**: Vercel or Netlify
- **Backend**: Railway, Render, or DigitalOcean App Platform
- **Database**: Supabase (managed PostgreSQL)
- **File Storage**: Supabase Storage or AWS S3

### Deployment Checklist

- [ ] Set up production Supabase project
- [ ] Configure environment variables
- [ ] Set up CORS for production domains
- [ ] Configure authentication redirects
- [ ] Set up file storage policies
- [ ] Configure monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📖 **Documentation**: See [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- 🐛 **Issues**: Create an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original Flask/vanilla JS implementation
- Carnegie Mellon University for the research foundation
- Supabase for the excellent backend-as-a-service platform
- The open-source community for the amazing tools and libraries 
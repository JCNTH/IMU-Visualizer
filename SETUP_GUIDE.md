# MBL IMUViz Setup Guide with Supabase

This guide will walk you through setting up the complete MBL IMUViz application with Supabase as the database backend.

## Prerequisites

- **Node.js 18+** and **pnpm**
- **Python 3.10+**
- **Supabase account** (free tier available)
- **Git**

## 1. Supabase Setup

### Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose your organization
4. Fill in project details:
   - **Name**: `mbl-imuviz` (or your preferred name)
   - **Database Password**: Create a strong password
   - **Region**: Choose closest to your location
5. Click "Create new project"

### Step 2: Get Your Project Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://your-project-ref.supabase.co`)
   - **Project API Keys**:
     - **anon public** key
     - **service_role** key (keep this secret!)

### Step 3: Run Database Migration

1. In your Supabase project dashboard, go to **SQL Editor**
2. Copy the contents of `supabase/migrations/001_initial_schema.sql`
3. Paste it in the SQL editor and run it
4. This will create all necessary tables and set up Row Level Security

## 2. Backend Setup

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Create Python Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -e .
```

### Step 4: Configure Environment Variables
```bash
cp env.example .env
```

Edit `.env` with your actual values:
```bash
# API Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# File Storage
UPLOAD_DIR=uploads
STATIC_DIR=static
MAX_FILE_SIZE=50MB

# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here

# Database
DATABASE_URL=postgresql://postgres:your-password@db.your-project-ref.supabase.co:5432/postgres

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET=your-jwt-secret-key

# External Services (optional)
OPENAI_API_KEY=your-openai-api-key-if-needed
OPENSIM_PATH=/path/to/opensim/installation

# Environment
ENVIRONMENT=development
```

### Step 5: Start the Backend
```bash
python run.py
```

The backend API will be available at `http://localhost:8000`

## 3. Frontend Setup

### Step 1: Navigate to Frontend Directory
```bash
cd frontend
```

### Step 2: Install Dependencies
```bash
pnpm install
```

### Step 3: Configure Environment Variables
```bash
cp env.example .env.local
```

Edit `.env.local` with your actual values:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Environment
NODE_ENV=development
NEXT_PUBLIC_ENVIRONMENT=development
```

### Step 4: Start the Frontend
```bash
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## 4. Authentication Setup (Optional)

### Enable Email Authentication in Supabase

1. In your Supabase project, go to **Authentication** → **Settings**
2. Under **Auth Providers**, ensure **Email** is enabled
3. Configure email templates if desired
4. Set up SMTP settings for email delivery (or use Supabase's built-in service)

### Configure Authentication URLs

In Supabase **Authentication** → **URL Configuration**:
- **Site URL**: `http://localhost:3000` (development) or your production URL
- **Redirect URLs**: Add your callback URLs

## 5. File Storage Setup

### Configure Supabase Storage

1. Go to **Storage** in your Supabase dashboard
2. Create a new bucket called `imu-data`
3. Set appropriate policies for file access
4. Update your environment variables if needed

## 6. Production Deployment

### Backend Deployment (Railway/Render/DigitalOcean)

1. Push your code to GitHub
2. Connect your repository to your hosting service
3. Set environment variables in your hosting platform
4. Deploy the backend service

### Frontend Deployment (Vercel/Netlify)

1. Connect your GitHub repository
2. Set build command: `pnpm build`
3. Set environment variables
4. Deploy

### Environment Variables for Production

Make sure to update:
- `CORS_ORIGINS` - Add your production frontend URL
- `NEXT_PUBLIC_API_URL` - Point to your production backend
- All Supabase URLs should remain the same
- Update `ENVIRONMENT` to `production`

## 7. Testing the Setup

### Verify Backend
1. Visit `http://localhost:8000/docs` to see the API documentation
2. Test the health endpoint: `http://localhost:8000/`

### Verify Frontend
1. Visit `http://localhost:3000`
2. Try uploading a sensor mapping file
3. Check browser console for any errors

### Verify Database Connection
1. In Supabase dashboard, go to **Table Editor**
2. You should see all the created tables
3. Try creating a test project through the API

## 8. Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (`python --version`)
- Ensure virtual environment is activated
- Verify all environment variables are set
- Check for port conflicts

**Frontend won't start:**
- Check Node.js version (`node --version`)
- Try deleting `node_modules` and running `pnpm install` again
- Check for port conflicts

**Database connection issues:**
- Verify Supabase credentials
- Check if your IP is allowed (Supabase allows all by default)
- Ensure the database migration ran successfully

**CORS errors:**
- Verify `CORS_ORIGINS` includes your frontend URL
- Check that both services are running

### Getting Help

1. Check the browser console for frontend errors
2. Check the terminal output for backend errors
3. Review Supabase logs in the dashboard
4. Ensure all environment variables are properly set

## 9. Development Workflow

### Making Database Changes

1. Create new migration files in `supabase/migrations/`
2. Run migrations through Supabase SQL Editor
3. Update your SQLModel definitions in `backend/src/api/database/models.py`

### Adding New Features

1. **Backend**: Add new endpoints in `main.py` or create new routers
2. **Frontend**: Add new components and update the store
3. **Database**: Create migrations for new tables/columns

This setup provides a production-ready foundation for the MBL IMUViz application with proper authentication, database management, and scalable architecture. 
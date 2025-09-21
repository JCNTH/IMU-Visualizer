-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE task_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Users table (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sensor mappings table
CREATE TABLE sensor_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    mapping_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calibration tasks table
CREATE TABLE calibration_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    selected_sensors TEXT[] DEFAULT '{}',
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sensor data table
CREATE TABLE sensor_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    calibration_task_id UUID REFERENCES calibration_tasks(id) ON DELETE SET NULL,
    sensor_name TEXT NOT NULL,
    sensor_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    data_type TEXT NOT NULL CHECK (data_type IN ('calibration', 'main_task')),
    processed_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- IK processing table
CREATE TABLE ik_processing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL DEFAULT '{}',
    status task_status DEFAULT 'pending',
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Video generation table
CREATE TABLE video_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ik_processing_id UUID NOT NULL REFERENCES ik_processing(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL DEFAULT '{}',
    status task_status DEFAULT 'pending',
    video_path TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for better performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_sensor_mappings_project_id ON sensor_mappings(project_id);
CREATE INDEX idx_calibration_tasks_project_id ON calibration_tasks(project_id);
CREATE INDEX idx_sensor_data_project_id ON sensor_data(project_id);
CREATE INDEX idx_sensor_data_calibration_task_id ON sensor_data(calibration_task_id);
CREATE INDEX idx_ik_processing_project_id ON ik_processing(project_id);
CREATE INDEX idx_video_generations_ik_processing_id ON video_generations(ik_processing_id);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ik_processing ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_generations ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Projects policies
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create projects" ON projects
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Sensor mappings policies
CREATE POLICY "Users can view own sensor mappings" ON sensor_mappings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = sensor_mappings.project_id 
            AND projects.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can create sensor mappings" ON sensor_mappings
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = sensor_mappings.project_id 
            AND projects.user_id::text = auth.uid()::text
        )
    );

-- Similar policies for other tables (calibration_tasks, sensor_data, ik_processing, video_generations)
-- Following the same pattern of checking project ownership through joins

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calibration_tasks_updated_at BEFORE UPDATE ON calibration_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ik_processing_updated_at BEFORE UPDATE ON ik_processing
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_video_generations_updated_at BEFORE UPDATE ON video_generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 
-- Manuscriptify Database Schema for Supabase
-- Create tables based on original spec requirements

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'premium', 'lifetime')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    credits_remaining INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Book projects table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    description TEXT DEFAULT '',
    genre TEXT NOT NULL CHECK (genre IN ('ebook', 'novel', 'kids_story', 'coloring_book')),
    content TEXT DEFAULT '',
    generated_content TEXT DEFAULT '',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'completed', 'failed')),
    
    -- Genre-specific settings
    page_size TEXT DEFAULT '6x9', -- '6x9' or '8x10'
    min_pages INTEGER,
    max_pages INTEGER,
    target_language TEXT DEFAULT 'en',
    include_images BOOLEAN DEFAULT FALSE,
    voice_style TEXT DEFAULT 'neutral',
    
    -- Generated assets
    cover_image_url TEXT,
    audio_file_url TEXT,
    pdf_url TEXT,
    
    -- Processing metadata
    progress INTEGER DEFAULT 0,
    processing_logs JSONB DEFAULT '[]'::jsonb,
    word_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- File uploads table
CREATE TABLE IF NOT EXISTS public.file_uploads (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    extracted_text TEXT,
    word_count INTEGER DEFAULT 0,
    upload_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscription plans table
CREATE TABLE IF NOT EXISTS public.subscription_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    price_lifetime DECIMAL(10,2),
    credits_per_month INTEGER DEFAULT 0,
    max_projects INTEGER DEFAULT 10,
    features JSONB DEFAULT '{}'::jsonb,
    stripe_price_id_monthly TEXT,
    stripe_price_id_yearly TEXT,
    stripe_product_id TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions table
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES public.subscription_plans(id),
    stripe_subscription_id TEXT UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'past_due', 'incomplete')),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing jobs table for background tasks
CREATE TABLE IF NOT EXISTS public.processing_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL CHECK (job_type IN ('content_generation', 'audio_generation', 'cover_generation', 'translation')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0,
    result_data JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default subscription plans
INSERT INTO public.subscription_plans (name, price_monthly, price_yearly, price_lifetime, credits_per_month, max_projects, features)
VALUES 
    ('Free', 0, 0, 0, 5, 3, '{"audiobook_generation": false, "cover_art": false, "ai_enhancement": false}'),
    ('Pro', 19.99, 199.99, NULL, 50, 25, '{"audiobook_generation": true, "cover_art": true, "ai_enhancement": true, "priority_support": false}'),
    ('Premium', 39.99, 399.99, NULL, 150, 100, '{"audiobook_generation": true, "cover_art": true, "ai_enhancement": true, "priority_support": true, "bulk_export": true}'),
    ('Lifetime', NULL, NULL, 199.00, 999999, 999999, '{"audiobook_generation": true, "cover_art": true, "ai_enhancement": true, "priority_support": true, "bulk_export": true, "lifetime_access": true}')
ON CONFLICT DO NOTHING;

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own data
CREATE POLICY "Users can only see own data" ON public.users FOR ALL USING (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users can see own projects" ON public.projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own projects" ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects" ON public.projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects" ON public.projects FOR DELETE USING (auth.uid() = user_id);

-- File uploads policies
CREATE POLICY "Users can see own uploads" ON public.file_uploads FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own uploads" ON public.file_uploads FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own uploads" ON public.file_uploads FOR DELETE USING (auth.uid() = user_id);

-- User subscriptions policies  
CREATE POLICY "Users can see own subscriptions" ON public.user_subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own subscriptions" ON public.user_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Processing jobs policies
CREATE POLICY "Users can see own jobs" ON public.processing_jobs 
FOR SELECT USING (auth.uid() = (SELECT user_id FROM public.projects WHERE id = project_id));

-- Create functions and triggers for updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER handle_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_user_subscriptions_updated_at
    BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
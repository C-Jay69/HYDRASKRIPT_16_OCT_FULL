# Manuscriptify - AI-Powered Audiobook Platform

## Project Overview
Manuscriptify is a full-stack application for AI-powered audiobook and ebook generation. The project has been successfully imported and configured to run in the Replit environment.

## Project Structure
- **Frontend**: React application with modern UI components using Tailwind CSS
- **Backend**: FastAPI Python server providing REST API endpoints
- **Database**: PostgreSQL (configured for Replit environment)

## Current Setup Status
✅ **Languages Installed**: Python 3.11, Node.js 20  
✅ **Dependencies Installed**: All frontend and backend dependencies + Supabase, Stripe  
✅ **Database Configured**: PostgreSQL database with full schema deployed  
✅ **Frontend Server**: Running on port 5000 with brand colors and professional UI  
✅ **Backend Server**: Running on port 8000 with full FastAPI + Database integration  
✅ **Environment Variables**: Complete API integration configured  
✅ **Deployment**: Configured for autoscale deployment  

## Key Configurations Made for Replit
1. **Frontend Dev Server**: Configured to allow all hosts (`allowedHosts: 'all'`) and bind to `0.0.0.0:5000`
2. **Backend API**: Simplified server running on port 8000 with CORS enabled for all origins
3. **Environment Variables**: `REACT_APP_BACKEND_URL` set to point to backend server
4. **Dependencies**: Fixed AJV version conflicts and date-fns compatibility issues

## Current Functionality
- **Health Check API**: Backend health endpoint responding correctly
- **Mock Authentication**: Login/register endpoints with demo data
- **File Type Support**: Configured for TXT, PDF, DOCX file uploads
- **UI Components**: Complete React component library with authentication modal

## External Services (Currently Mocked)
The original project includes integrations with external AI services:
- **AI Content Generation**: Uses Emergent LLM API
- **Audio Generation**: Fish Audio API integration
- **Image Generation**: Fal.ai API for cover art
- **Translation**: DeepL API integration

These services are currently mocked in the simple server for development purposes.

## Development Status
- Frontend and backend are running successfully
- Database is connected and ready
- Basic API endpoints are functional
- Ready for further development and external service integration

## Recent Changes
- **Date**: September 27, 2025
- **Action**: Complete backend migration to production-ready architecture
- **Major Updates**:
  - Replaced simple mock server with full FastAPI + PostgreSQL backend
  - Implemented complete database schema with users, projects, subscriptions tables
  - Added Supabase and Stripe integrations for production scalability
  - Created comprehensive API endpoints for authentication, projects, payments
  - Applied brand colors (#0000FF, #FFBF00, #FF00FF, #00FFFF, #DCDFD5) throughout UI
  - Configured genre-specific constraints (ebook, novel, kids story, coloring book)
  - Set up proper CORS and environment configuration for Replit deployment

## User Preferences
- **Environment**: Replit cloud development
- **Focus**: Full-stack web application development
- **Stack**: React + FastAPI + PostgreSQL
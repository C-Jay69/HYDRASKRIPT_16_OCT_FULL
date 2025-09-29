import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { UserContext } from '../App';

function Dashboard() {
  const { user } = useContext(UserContext);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    processing: 0
  });

  useEffect(() => {
    if (user) {
      fetchProjects();
    }
  }, [user]);

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/projects');
      const projectList = response.data;
      
      setProjects(projectList);
      
      // Calculate stats
      const stats = {
        total: projectList.length,
        completed: projectList.filter(p => p.status === 'completed').length,
        processing: projectList.filter(p => p.status === 'processing').length
      };
      setStats(stats);
      
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project?')) {
      return;
    }

    try {
      await axios.delete(`/api/projects/${projectId}`);
      setProjects(projects.filter(p => p.id !== projectId));
      toast.success('Project deleted successfully');
    } catch (error) {
      toast.error('Failed to delete project');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="user-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user?.full_name || user?.email}!</p>
        </div>
        <Link
          to="/create"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          data-testid="create-new-project-btn"
        >
          + New Project
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard
          title="Total Projects"
          value={stats.total}
          icon="📚"
          color="bg-blue-500"
        />
        <StatsCard
          title="Completed"
          value={stats.completed}
          icon="✅"
          color="bg-green-500"
        />
        <StatsCard
          title="In Progress"
          value={stats.processing}
          icon="⏳"
          color="bg-yellow-500"
        />
      </div>

      {/* Projects List */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Projects</h2>
        
        {projects.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={() => handleDeleteProject(project.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Stats Card Component
function StatsCard({ title, value, icon, color }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

// Project Card Component
function ProjectCard({ project, onDelete }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700';
      case 'processing': return 'bg-yellow-100 text-yellow-700';
      case 'failed': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getGenreColor = (genre) => {
    switch (genre) {
      case 'ebook': return 'bg-blue-500';
      case 'novel': return 'bg-purple-500';
      case 'kids_story': return 'bg-green-500';
      case 'coloring_book': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow card-hover">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 ${getGenreColor(project.settings?.genre)} rounded-lg flex items-center justify-center text-white font-bold`}>
            {project.title.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-lg">{project.title}</h3>
            <p className="text-sm text-gray-500">{project.settings?.genre?.replace('_', ' ')}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
            {project.status}
          </span>
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
      )}

      {/* Progress */}
      {project.status === 'processing' && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{project.progress || 0}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="progress-bar h-2 rounded-full" 
              style={{ width: `${project.progress || 0}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          Created {formatDate(project.created_at)}
        </div>
        <div className="flex items-center space-x-2">
          {project.status === 'processing' && (
            <Link
              to={`/progress/${project.id}`}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              View Progress
            </Link>
          )}
          <Link
            to={`/project/${project.id}`}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            {project.status === 'completed' ? 'View' : 'Edit'}
          </Link>
          <button
            onClick={onDelete}
            className="text-red-600 hover:text-red-700 text-sm font-medium ml-2"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

// Empty State Component
function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="w-24 h-24 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
        <svg className="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">No projects yet</h3>
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        Create your first book project to get started with AI-powered content generation.
      </p>
      <Link
        to="/create"
        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-block"
      >
        Create Your First Project
      </Link>
    </div>
  );
}

export default Dashboard;
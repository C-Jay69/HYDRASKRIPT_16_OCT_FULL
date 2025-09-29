import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminStats();
  }, []);

  const fetchAdminStats = async () => {
    try {
      const response = await axios.get('/api/admin/stats');
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load admin statistics');
    } finally {
      setLoading(false);
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
    <div className="space-y-8" data-testid="admin-panel">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-1">System overview and statistics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon="👥"
          color="bg-blue-500"
        />
        <StatCard
          title="Total Projects"
          value={stats?.total_projects || 0}
          icon="📚"
          color="bg-green-500"
        />
        <StatCard
          title="Active Projects"
          value={stats?.active_projects || 0}
          icon="⚡"
          color="bg-yellow-500"
        />
        <StatCard
          title="Completed Projects"
          value={stats?.completed_projects || 0}
          icon="✅"
          color="bg-purple-500"
        />
      </div>

      {/* Popular Genres */}
      {stats?.popular_genres && Object.keys(stats.popular_genres).length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Popular Genres</h2>
          <div className="space-y-4">
            {Object.entries(stats.popular_genres)
              .sort(([,a], [,b]) => b - a)
              .map(([genre, count]) => (
                <div key={genre} className="flex items-center justify-between">
                  <span className="text-gray-700 capitalize">{genre?.replace('_', ' ')}</span>
                  <span className="text-gray-900 font-semibold">{count} projects</span>
                </div>
              ))
            }
          </div>
        </div>
      )}

      {/* System Status */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ServiceStatus name="API Server" status="healthy" />
          <ServiceStatus name="Database" status="healthy" />
          <ServiceStatus name="AI Service" status="healthy" />
          <ServiceStatus name="File Storage" status="healthy" />
          <ServiceStatus name="Audio Processing" status="healthy" />
          <ServiceStatus name="Image Generation" status="warning" note="Limited API credits" />
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, icon, color }) {
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

// Service Status Component
function ServiceStatus({ name, status, note }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  return (
    <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
      <div className="flex items-center space-x-3">
        <span className="text-lg">{getStatusIcon(status)}</span>
        <div>
          <p className="font-medium text-gray-900">{name}</p>
          {note && <p className="text-xs text-gray-500">{note}</p>}
        </div>
      </div>
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
        {status}
      </span>
    </div>
  );
}

export default AdminPanel;
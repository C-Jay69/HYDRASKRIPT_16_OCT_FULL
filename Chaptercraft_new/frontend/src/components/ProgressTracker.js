import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

function ProgressTracker() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (projectId) {
      fetchProgress();
      const interval = setInterval(fetchProgress, 2000);
      return () => clearInterval(interval);
    }
  }, [projectId]);

  const fetchProgress = async () => {
    try {
      const response = await axios.get(`/api/progress/${projectId}`);
      setProgress(response.data);
      setError(null);
      
      if (response.data.overall_progress === 100) {
        setTimeout(() => {
          navigate(`/project/${projectId}`);
        }, 2000);
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setError('Progress tracking not found for this project');
      } else {
        setError('Failed to fetch progress');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = (step) => {
    if (step.status === 'completed') {
      return (
        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    } else if (step.status === 'in_progress') {
      return (
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        </div>
      );
    } else {
      return (
        <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
          <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
        </div>
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading progress...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Progress Not Found</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8" data-testid="progress-tracker">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Processing Your Book</h1>
        <p className="text-gray-600">
          Your book is being generated using AI. This process may take a few minutes.
        </p>
      </div>

      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div className="text-center mb-6">
          <div className="text-4xl font-bold text-blue-600 mb-2">
            {progress?.overall_progress || 0}%
          </div>
          <p className="text-lg font-medium text-gray-900">
            {progress?.current_step || 'Initializing...'}
          </p>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-gradient-to-r from-blue-600 to-purple-600 h-3 rounded-full transition-all duration-500" 
            style={{ width: `${progress?.overall_progress || 0}%` }}
          ></div>
        </div>
      </div>

      {progress?.steps && progress.steps.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Processing Steps</h2>
          
          <div className="space-y-4">
            {progress.steps.map((step, index) => (
              <div key={index} className="flex items-start space-x-4">
                {getStepIcon(step)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900">
                      {step.step_name}
                    </h3>
                    <span className="text-xs text-gray-500">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{step.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {progress?.overall_progress === 100 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-green-900 mb-2">Processing Complete!</h2>
          <p className="text-green-700 mb-4">
            Your book has been successfully generated. Redirecting to project view...
          </p>
          <div className="flex items-center justify-center">
            <div className="w-4 h-4 border-2 border-green-600 border-t-transparent rounded-full animate-spin mr-2"></div>
            <span className="text-green-700">Redirecting...</span>
          </div>
        </div>
      )}

      <div className="flex justify-center space-x-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          Back to Dashboard
        </button>
        {progress?.overall_progress === 100 && (
          <button
            onClick={() => navigate(`/project/${projectId}`)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            data-testid="view-project-btn"
          >
            View Project
          </button>
        )}
      </div>
    </div>
  );
}

export default ProgressTracker;
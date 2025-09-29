import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

// Kids Story Preview Component for displaying images with story content
function KidsStoryPreview({ content }) {
  if (!content) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No content to preview yet. Generate a story to see it here!</p>
      </div>
    );
  }

  // Parse the content to extract images and text
  const parseStoryContent = (text) => {
    const parts = [];
    const lines = text.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check if line starts with a Pollination.ai URL (more specific check)
      if (line.startsWith('https://image.pollinations.ai/')) {
        // Extract the complete URL (handle URLs that might contain spaces or special chars)
        const urlMatch = line.match(/^(https:\/\/image\.pollinations\.ai\/[^\s]*)/);
        if (urlMatch) {
          parts.push({
            type: 'image',
            content: urlMatch[1],
            caption: ''
          });
        }
      } else if (line.includes('https://picsum.photos/') ||
                 (line.includes('http') && (line.includes('.jpg') || line.includes('.png') || line.includes('.gif')))) {
        // Handle other image URLs
        const urlMatch = line.match(/(https?:\/\/[^\s]+)/);
        if (urlMatch) {
          parts.push({
            type: 'image',
            content: urlMatch[0],
            caption: line.replace(urlMatch[0], '').trim()
          });
        }
      } else if (line.startsWith('# ')) {
        // Main title
        parts.push({
          type: 'title',
          content: line.replace('# ', '')
        });
      } else if (line.startsWith('## ') || line.startsWith('Page ')) {
        // Page headers
        parts.push({
          type: 'page-header',
          content: line.replace('## ', '').replace('Page ', 'Page ')
        });
      } else if (line.length > 0) {
        // Regular text content
        parts.push({
          type: 'text',
          content: line
        });
      }
    }
    
    return parts;
  };

  const storyParts = parseStoryContent(content);

  return (
    <div className="kids-story-preview bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6 max-h-96 overflow-y-auto">
      <div className="space-y-6">
        {storyParts.map((part, index) => {
          switch (part.type) {
            case 'title':
              return (
                <h1 key={index} className="text-3xl font-bold text-center text-purple-800 mb-8">
                  {part.content}
                </h1>
              );
            
            case 'page-header':
              return (
                <h2 key={index} className="text-xl font-semibold text-blue-700 mt-8 mb-4 border-b-2 border-blue-200 pb-2">
                  {part.content}
                </h2>
              );
            
            case 'image':
              return (
                <div key={index} className="flex justify-center my-6">
                  <div className="max-w-md">
                    <img
                      src={part.content}
                      alt={part.caption || `Story illustration ${index}`}
                      className="w-full h-auto rounded-lg shadow-lg border-4 border-white"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                    {part.caption && (
                      <p className="text-sm text-gray-600 text-center mt-2 italic">
                        {part.caption}
                      </p>
                    )}
                  </div>
                </div>
              );
            
            case 'text':
              return (
                <p key={index} className="text-gray-800 leading-relaxed text-lg">
                  {part.content}
                </p>
              );
            
            default:
              return null;
          }
        })}
      </div>
      
      {storyParts.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>Story content is being processed...</p>
        </div>
      )}
    </div>
  );
}

function ProjectEditor() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('content');
  const [audioGenerating, setAudioGenerating] = useState(false);
  const [coverGenerating, setCoverGenerating] = useState(false);
  const [viewMode, setViewMode] = useState('edit'); // 'edit' or 'preview'

  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (projectId) {
      fetchProject();
    }
  }, [projectId]);

  const fetchProject = async () => {
    try {
      const response = await axios.get(`/api/projects/detail/${projectId}`);
      const projectData = response.data;
      
      setProject(projectData);
      setContent(projectData.generated_content || projectData.content || '');
      setTitle(projectData.title || '');
      setAuthor(projectData.author || '');
      setDescription(projectData.description || '');
    } catch (error) {
      toast.error('Failed to load project');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      await axios.put(`/api/projects/${projectId}`, {
        title,
        author,
        description,
        content
      });
      
      toast.success('Project saved successfully!');
      
      setProject(prev => ({
        ...prev,
        title,
        author,
        description,
        content
      }));
      
    } catch (error) {
      toast.error('Failed to save project');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!content.trim()) {
      toast.error('Please add content before generating audio');
      return;
    }

    try {
      setAudioGenerating(true);
      
      const response = await axios.post(`/api/audio/generate-audiobook/${projectId}`, {
        voice_style: 'narrator',
        speed: 1.0
      });
      
      toast.success('Audiobook generation started! Check progress in dashboard.');
      navigate(`/progress/${projectId}`);
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to generate audiobook';
      toast.error(message);
    } finally {
      setAudioGenerating(false);
    }
  };

  const handleGenerateCover = async () => {
    if (!title.trim()) {
      toast.error('Please add a title before generating cover art');
      return;
    }

    try {
      setCoverGenerating(true);
      
      const response = await axios.post('/api/images/generate-cover', {
        title,
        genre: project.settings?.genre || 'ebook',
        description: description || 'A compelling book cover',
        style: 'professional'
      });
      
      if (response.data.success) {
        toast.success('Cover art generated successfully!');
        setProject(prev => ({
          ...prev,
          cover_image_url: response.data.image_url
        }));
      } else {
        toast.error('Cover generation failed: ' + response.data.error);
      }
      
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to generate cover art';
      toast.error(message);
    } finally {
      setCoverGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Project Not Found</h2>
        <button
          onClick={() => navigate('/dashboard')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6" data-testid="project-editor">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{title || 'Untitled Project'}</h1>
          <p className="text-gray-600 mt-1">
            {project.settings?.genre?.replace('_', ' ')} • {project.status}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
            data-testid="save-project-btn"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="border border-gray-300 text-gray-700 px-6 py-2 rounded-lg font-medium hover:bg-gray-50"
          >
            Back
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {['content', 'details', 'media'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'content' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Content Editor</h2>
                {(() => {
                  // Show Edit/Preview toggle for any content with images or kids stories
                  const hasImages = /https?:\/\/image\.pollinations\.ai\//.test(content);
                  const isKidsStory = project?.settings?.genre === 'kids_story';
                  const showToggle = hasImages || isKidsStory;
                  
                  return showToggle && (
                    <div className="flex bg-gray-100 rounded-lg p-1">
                      <button
                        onClick={() => setViewMode('edit')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                          viewMode === 'edit' 
                            ? 'bg-white text-blue-600 shadow-sm' 
                            : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => setViewMode('preview')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                          viewMode === 'preview' 
                            ? 'bg-white text-blue-600 shadow-sm' 
                            : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        Preview
                      </button>
                    </div>
                  );
                })()}
              </div>
            </div>
            <div className="p-4">
              {(() => {
                // Check if content contains Pollination.ai image URLs
                const hasPollinations = /https?:\/\/image\.pollinations\.ai\//.test(content);
                const showImagePreview = hasPollinations || viewMode === 'preview';
                
                return showImagePreview ? (
                  <KidsStoryPreview content={content} />
                ) : (
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={20}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Start writing your book content here..."
                    data-testid="content-textarea"
                  />
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'details' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Project Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter book title"
                  data-testid="title-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Author
                </label>
                <input
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter author name"
                  data-testid="author-input"
                />
              </div>
            </div>
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Describe your book"
                data-testid="description-input"
              />
            </div>
            
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Genre
                  </label>
                  <p className="text-sm text-gray-600 capitalize">
                    {project.settings?.genre?.replace('_', ' ') || 'Not specified'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <p className="text-sm text-gray-600">
                    {project.settings?.target_language === 'en' ? 'English' : project.settings?.target_language || 'Not specified'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Page Size
                  </label>
                  <p className="text-sm text-gray-600">
                    {project.settings?.page_size || 'Not specified'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'media' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Cover Art</h2>
              <button
                onClick={handleGenerateCover}
                disabled={coverGenerating}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                data-testid="generate-cover-btn"
              >
                {coverGenerating ? (
                  <div className="flex items-center">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Generating...
                  </div>
                ) : (
                  '🎨 Generate Cover'
                )}
              </button>
            </div>
            
            {project.cover_image_url ? (
              <div className="flex items-start space-x-6">
                <img
                  src={project.cover_image_url}
                  alt="Book Cover"
                  className="w-48 h-64 object-cover rounded-lg shadow-md"
                />
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-2">Generated Cover</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    AI-generated cover art based on your book title and genre.
                  </p>
                  <button
                    onClick={handleGenerateCover}
                    disabled={coverGenerating}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Regenerate Cover
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-gray-600 mb-2">No cover art generated yet</p>
                <p className="text-sm text-gray-500">Click Generate Cover to create AI-powered cover art</p>
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Audiobook</h2>
              <button
                onClick={handleGenerateAudio}
                disabled={audioGenerating}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                data-testid="generate-audio-btn"
              >
                {audioGenerating ? (
                  <div className="flex items-center">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Generating...
                  </div>
                ) : (
                  '🎧 Generate Audiobook'
                )}
              </button>
            </div>
            
            {project.audio_file_url ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.825L4.5 14H2a1 1 0 01-1-1V7a1 1 0 011-1h2.5l3.883-2.825z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Audiobook Generated</h3>
                    <p className="text-sm text-gray-600">Your audiobook is ready for download</p>
                  </div>
                </div>
                <audio controls className="w-full">
                  <source src={project.audio_file_url} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                </div>
                <p className="text-gray-600 mb-2">No audiobook generated yet</p>
                <p className="text-sm text-gray-500">Click Generate Audiobook to create AI-powered audio narration</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectEditor;
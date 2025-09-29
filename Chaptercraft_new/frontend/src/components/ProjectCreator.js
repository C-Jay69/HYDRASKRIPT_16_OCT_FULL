import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useDropzone } from 'react-dropzone';
import { UserContext } from '../App';

function ProjectCreator() {
  const navigate = useNavigate();
  const { user } = useContext(UserContext);
  const [activeTab, setActiveTab] = useState('prompt');
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    description: '',
    genre: 'ebook',
    target_language: 'en',
    content: '',
    prompt: '',
    length: 'medium',
    style: 'engaging'
  });
  
  const [uploadedFile, setUploadedFile] = useState(null);

  const genreConfig = {
    ebook: {
      name: 'E-book',
      description: 'Professional non-fiction books, guides, and educational content',
      specs: '75-150 pages • 6x9 format',
      color: 'bg-blue-500',
      maxPages: 150,
      minPages: 75
    },
    novel: {
      name: 'Novel',
      description: 'Fiction stories with compelling characters and narrative',
      specs: '100-250 pages • 6x9 format',
      color: 'bg-purple-500',
      maxPages: 250,
      minPages: 100
    },
    kids_story: {
      name: 'Kids Story',
      description: 'Illustrated children books with engaging artwork',
      specs: 'Up to 25 pages • 8x10 format',
      color: 'bg-green-500',
      maxPages: 25,
      minPages: 1
    },
    coloring_book: {
      name: 'Coloring Book',
      description: 'Black & white illustrations perfect for coloring',
      specs: '20 pages • 8x10 format',
      color: 'bg-orange-500',
      maxPages: 20,
      minPages: 20
    },
    audiobook: {
      name: 'Audiobook',
      description: 'Professional narrated audio content with natural voice synthesis',
      specs: '2-8 hours runtime • MP3 format',
      color: 'bg-red-500',
      maxPages: 200,
      minPages: 50
    }
  };

  const languages = {
    en: 'English',
    fr: 'French',
    es: 'Spanish',
    zh: 'Chinese (Mandarin)',
    hi: 'Hindi',
    ja: 'Japanese'
  };

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadedFile(response.data);
      setFormData(prev => ({
        ...prev,
        content: response.data.extracted_text,
        title: prev.title || file.name.replace(/\.[^/.]+$/, '')
      }));
      
      toast.success('File uploaded and processed successfully!');
    } catch (error) {
      const message = error.response?.data?.detail || 'File upload failed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 25 * 1024 * 1024,
    multiple: false
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error('Please enter a project title');
      return;
    }

    // Special validation for audiobooks
    if (formData.genre === 'audiobook' && activeTab === 'prompt') {
      if (!uploadedFile && !formData.prompt.trim()) {
        toast.error('Please either upload a manuscript or enter a prompt for your audiobook');
        return;
      }
    } else if (activeTab === 'prompt' && !formData.prompt.trim()) {
      toast.error('Please enter a prompt for book generation');
      return;
    }

    if (activeTab === 'upload' && !formData.content.trim()) {
      toast.error('Please upload a file or enter content');
      return;
    }

    try {
      setLoading(true);

      const projectData = {
        title: formData.title,
        author: formData.author || '',
        description: formData.description || '',
        genre: formData.genre,
        target_language: formData.target_language,
        voice_style: 'neutral',
        content: activeTab === 'upload' ? formData.content : (uploadedFile?.extracted_text || formData.prompt || '')
      };

      const response = await axios.post('/api/projects', projectData);

      const projectId = response.data.project_id;

      if (activeTab === 'prompt' || (activeTab === 'upload' && formData.genre === 'audiobook')) {
        // For audiobooks with uploaded manuscripts, use the extracted text
        const isUploadedAudiobook = formData.genre === 'audiobook' && uploadedFile?.extracted_text;
        
        const generateRequest = {
          project_id: projectId,
          prompt: isUploadedAudiobook ? '' : formData.prompt,
          uploaded_content: isUploadedAudiobook ? uploadedFile.extracted_text : null,
          genre: formData.genre,
          target_language: formData.target_language,
          length: formData.length,
          style: formData.style
        };

        await axios.post('/api/ai/generate-book', generateRequest);
        
        const message = isUploadedAudiobook 
          ? 'Project created! Audio conversion started.' 
          : 'Project created! AI generation started.';
        
        toast.success(message);
        navigate(`/progress/${projectId}`);
      } else {
        toast.success('Project created successfully!');
        navigate(`/project/${projectId}`);
      }

    } catch (error) {
      console.error('Project creation error:', error);
      let message = 'Failed to create project';
      
      if (error.response?.data?.detail) {
        // Handle string errors
        if (typeof error.response.data.detail === 'string') {
          message = error.response.data.detail;
        }
        // Handle validation errors array
        else if (Array.isArray(error.response.data.detail)) {
          message = error.response.data.detail.map(err => {
            if (typeof err === 'string') return err;
            if (err.msg) return `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`;
            return JSON.stringify(err);
          }).join(', ');
        }
        // Handle objects
        else if (typeof error.response.data.detail === 'object') {
          message = JSON.stringify(error.response.data.detail);
        }
      }
      
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Create New Project</h1>
        <p className="text-gray-600 text-lg">
          Start your book creation journey with AI-powered content generation
        </p>
      </div>

      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('prompt')}
          className={`py-3 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'prompt'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Generate from Prompt
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`py-3 px-6 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'upload'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload Content
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {formData.genre === 'coloring_book' ? 'Image Theme *' : 'Project Title *'}
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={
                  formData.genre === 'coloring_book' 
                    ? "e.g., Exotic Animals, Mandalas, Underwater Scenes, Fantasy Creatures"
                    : "Enter your book title"
                }
                required
                data-testid="project-title-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Author Name
              </label>
              <input
                type="text"
                name="author"
                value={formData.author}
                onChange={handleInputChange}
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
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Describe your book project"
              data-testid="description-input"
            />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Book Genre</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(genreConfig).map(([key, config]) => (
              <div
                key={key}
                onClick={() => setFormData(prev => ({ ...prev, genre: key }))}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  formData.genre === key
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                data-testid={`genre-${key}`}
              >
                <div className={`w-10 h-10 ${config.color} rounded-lg mb-3 flex items-center justify-center text-white font-bold`}>
                  {config.name.charAt(0)}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{config.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{config.description}</p>
                <p className="text-xs text-gray-500 font-medium">{config.specs}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Target Language</h2>
          <select
            name="target_language"
            value={formData.target_language}
            onChange={handleInputChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            data-testid="language-select"
          >
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </div>

        {activeTab === 'prompt' ? (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              {formData.genre === 'audiobook' ? 'Audiobook Settings' : 'AI Generation Settings'}
            </h2>
            <div className="space-y-6">
              {formData.genre === 'audiobook' ? (
                <div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Content Source *
                    </label>
                    <div className="flex space-x-4">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="audiobook_source"
                          value="prompt"
                          checked={!uploadedFile}
                          onChange={() => setUploadedFile(null)}
                          className="mr-2"
                        />
                        Generate from prompt
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="audiobook_source"
                          value="upload"
                          checked={!!uploadedFile}
                          onChange={() => {}}
                          className="mr-2"
                        />
                        Upload manuscript
                      </label>
                    </div>
                  </div>
                  
                  {!uploadedFile ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Audiobook Prompt *
                      </label>
                      <textarea
                        name="prompt"
                        value={formData.prompt}
                        onChange={handleInputChange}
                        rows={4}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Describe the content for your audiobook. This will be converted to professional narration..."
                        required
                        data-testid="prompt-input"
                      />
                    </div>
                  ) : (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-green-800">
                            Manuscript uploaded: {uploadedFile.filename}
                          </p>
                          <p className="text-sm text-green-600">
                            {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB • Ready for audio conversion
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setUploadedFile(null)}
                          className="ml-auto text-green-600 hover:text-green-800"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Book Prompt *
                  </label>
                  <textarea
                    name="prompt"
                    value={formData.prompt}
                    onChange={handleInputChange}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={
                      formData.genre === 'coloring_book' 
                        ? "Describe the style and theme for your coloring pages. e.g., 'Detailed mandala patterns with intricate geometric designs' or 'Cute farm animals in simple line art style'"
                        : "Describe what kind of book you want to create. Be as detailed as possible..."
                    }
                    required
                    data-testid="prompt-input"
                  />
                </div>
              )}
              
              {/* Length and Style options - only show for non-audiobook or prompt-based audiobooks */}
              {(formData.genre !== 'audiobook' || !uploadedFile) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Length
                    </label>
                    <select
                      name="length"
                      value={formData.length}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="short">Short</option>
                      <option value="medium">Medium</option>
                      <option value="long">Long</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Style
                    </label>
                    <select
                      name="style"
                      value={formData.style}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="engaging">Engaging</option>
                      <option value="professional">Professional</option>
                      <option value="creative">Creative</option>
                      <option value="educational">Educational</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              {formData.genre === 'audiobook' ? 'Upload Manuscript for Audio Conversion' : 'Upload Content'}
            </h2>
            
            <div className="mb-6">
              <div
                {...getRootProps()}
                className={`p-8 text-center cursor-pointer border-2 border-dashed rounded-lg transition-colors ${
                  isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} data-testid="file-upload-input" />
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      {isDragActive ? 'Drop your file here' : 
                       formData.genre === 'audiobook' ? 'Upload your book or manuscript' : 'Upload your document'}
                    </p>
                    <p className="text-gray-600">
                      {formData.genre === 'audiobook' 
                        ? 'Drag & drop or click to select • TXT, PDF, DOCX • Max 25MB • Will be converted to professional audio narration'
                        : 'Drag & drop or click to select • TXT, PDF, DOCX • Max 25MB'
                      }
                    </p>
                  </div>
                </div>
              </div>
              
              {uploadedFile && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-green-900">{uploadedFile.filename}</p>
                      <p className="text-sm text-green-600">
                        {uploadedFile.word_count} words • {(uploadedFile.file_size / 1024).toFixed(1)} KB
                        {formData.genre === 'audiobook' ? ' • Ready for audio conversion' : ''}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Or paste your content directly
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                rows={8}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Paste your book content here..."
                data-testid="content-textarea"
              />
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-semibold transition-colors"
            data-testid="create-project-btn"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Creating Project...
              </div>
            ) : (
              'Create Project'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ProjectCreator;
import React, { useState, useEffect } from 'react';
import { Search, Calendar, Tag, ExternalLink, Github, Zap } from 'lucide-react';

interface Changelog {
  id: number;
  version: string;
  title: string;
  content: string;
  created_at: string;
  published_at: string;
  is_published: boolean;
}

const API_BASE_URL = 'http://localhost:8000';

// Markdown renderer component
const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
  const renderMarkdown = (text: string) => {
    // Simple markdown parser for common elements
    let html = text
      // Headers
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-gray-800 mt-6 mb-3">$1</h3>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-gray-900 mt-8 mb-4">$1</h2>')
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-4">$1</h1>')
      // Bold and italic
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      // Code blocks
      .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 rounded-md p-3 my-3 overflow-x-auto"><code class="text-sm">$1</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">$1</a>')
      // Line breaks
      .replace(/\n/g, '<br />');

    // Handle bullet points
    const lines = html.split('<br />');
    let inList = false;
    const processedLines = [];

    for (let line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('- ')) {
        if (!inList) {
          processedLines.push('<ul class="list-disc ml-6 my-3 space-y-1">');
          inList = true;
        }
        processedLines.push(`<li class="text-gray-700">${trimmed.substring(2)}</li>`);
      } else {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        if (trimmed) {
          processedLines.push(`<p class="text-gray-700 mb-3">${line}</p>`);
        }
      }
    }

    if (inList) {
      processedLines.push('</ul>');
    }

    return processedLines.join('');
  };

  return (
    <div 
      className="prose prose-sm max-w-none"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
};

// Individual changelog entry component
const ChangelogEntry: React.FC<{ changelog: Changelog }> = ({ changelog }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            <Tag className="w-4 h-4 mr-1" />
            {changelog.version}
          </span>
          <h2 className="text-xl font-bold text-gray-900">{changelog.title}</h2>
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <Calendar className="w-4 h-4 mr-1" />
          {formatDate(changelog.published_at)}
        </div>
      </div>
      
      <div className="changelog-content">
        <MarkdownRenderer content={changelog.content} />
      </div>
    </div>
  );
};

// Loading skeleton component
const LoadingSkeleton: React.FC = () => (
  <div className="space-y-6">
    {[1, 2, 3].map((i) => (
      <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
            <div className="w-48 h-6 bg-gray-200 rounded"></div>
          </div>
          <div className="w-24 h-4 bg-gray-200 rounded"></div>
        </div>
        <div className="space-y-3">
          <div className="w-full h-4 bg-gray-200 rounded"></div>
          <div className="w-3/4 h-4 bg-gray-200 rounded"></div>
          <div className="w-1/2 h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    ))}
  </div>
);

// Empty state component
const EmptyState: React.FC = () => (
  <div className="text-center py-12">
    <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
    <h3 className="text-lg font-medium text-gray-900 mb-2">No changelogs yet</h3>
    <p className="text-gray-500 mb-6">
      Changelogs will appear here once they're published using the CLI tool.
    </p>
    <div className="bg-gray-50 rounded-lg p-4 text-left max-w-md mx-auto">
      <p className="text-sm font-medium text-gray-900 mb-2">Get started:</p>
      <code className="text-xs text-gray-600 block">
        changelog-gen generate<br />
        changelog-gen publish --version v1.0.0
      </code>
    </div>
  </div>
);

// Main App component
const App: React.FC = () => {
  const [changelogs, setChangelogs] = useState<Changelog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchChangelogs();
  }, []);

  const fetchChangelogs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/changelog`);
      if (!response.ok) {
        throw new Error('Failed to fetch changelogs');
      }
      const data = await response.json();
      setChangelogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const filteredChangelogs = changelogs.filter(changelog =>
    changelog.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    changelog.version.toLowerCase().includes(searchTerm.toLowerCase()) ||
    changelog.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Chronicler</h1>
                <p className="text-sm text-gray-600">Stay updated with our latest changes</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <a 
                href="https://github.com/anke-hao/Chronicler" 
                className="text-gray-500 hover:text-gray-700 transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="w-5 h-5" />
              </a>
              <a 
                href="/api/docs" 
                className="text-gray-500 hover:text-gray-700 transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Search */}
        {changelogs.length > 0 && (
          <div className="mb-8">
            <div className="relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search changelogs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              />
            </div>
          </div>
        )}

        {/* Content */}
        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <div className="text-center py-12">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
              <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Changelogs</h3>
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchChangelogs}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : filteredChangelogs.length === 0 ? (
          searchTerm ? (
            <div className="text-center py-12">
              <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-500">
                Try adjusting your search terms or{' '}
                <button
                  onClick={() => setSearchTerm('')}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  clear the search
                </button>
              </p>
            </div>
          ) : (
            <EmptyState />
          )
        ) : (
          <div className="space-y-6">
            {filteredChangelogs.map((changelog) => (
              <ChangelogEntry key={changelog.id} changelog={changelog} />
            ))}
          </div>
        )}

        {/* Stats Footer */}
        {changelogs.length > 0 && (
          <div className="mt-12 pt-8 border-t border-gray-200">
            <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <Tag className="w-4 h-4" />
                <span>{changelogs.length} releases</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4" />
                <span>
                  Latest: {changelogs.length > 0 ? new Date(changelogs[0].published_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>
              Generated with{' '}
              <span className="font-medium text-gray-900">Chronicler</span>
              {' • '}
              <a href="https://github.com/anke-hao/Chronicler" className="text-blue-600 hover:text-blue-800">
                View on GitHub
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { tokenizeLine } from './highlight';

function renderLine(line) {
  const tokens = tokenizeLine(line);
  if (!tokens.length) return '\u00A0';
  return tokens.map((t, i) =>
    t.cls ? (
      <span key={i} className={t.cls}>{t.text}</span>
    ) : (
      <React.Fragment key={i}>{t.text}</React.Fragment>
    )
  );
}

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [filename, setFilename] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const [chunksCount, setChunksCount] = useState(null);

  // Selection popup & explanation state
  const [selectionPopup, setSelectionPopup] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState('');

  // Theme state (light / dark), persisted to localStorage
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('retrievr-theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('retrievr-theme', theme);
  }, [theme]);

  // Abort controller ref for cancellation
  const abortControllerRef = useRef(null);

  const cancelExplanationRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setExplanationLoading(false);
  };

  // Dynamic viewer state
  const [isWrapped, setIsWrapped] = useState(true);
  const [fontSize, setFontSize] = useState(14);
  const [searchTerm, setSearchTerm] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setFilename(response.data.filename || selectedFile.name);
      setFileContent(response.data.code || '');
      setChunksCount(response.data.chunks_count ?? null);
    } catch (err) {
      console.error('Upload Error:', err);
      setError(
        err.response?.data?.message ||
        'Failed to upload and process file. Make sure the FastAPI server is running on http://localhost:8000'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (fileContent) {
      navigator.clipboard.writeText(fileContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Automatically hide popup and cancel pending request when text is deselected
  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        cancelExplanationRequest();
        setSelectionPopup(null);
      }
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, []);

  // Capture text selection made by the user
  const handleMouseUp = () => {
    const selection = window.getSelection();

    if (!selection || selection.isCollapsed) {
      cancelExplanationRequest();
      setSelectionPopup(null);
      return;
    }

    const selectedText = selection.toString().trim();

    if (!selectedText) {
      cancelExplanationRequest();
      setSelectionPopup(null);
      return;
    }

    // Calculate line and column numbers
    let startLine = 1;
    let startColumn = 1;
    let endLine = 1;
    let endColumn = 1;

    if (fileContent) {
      const charIndex = fileContent.indexOf(selectedText);

      if (charIndex !== -1) {
        const textBefore = fileContent.substring(0, charIndex);
        const linesBefore = textBefore.split('\n');

        startLine = linesBefore.length;
        startColumn = linesBefore[linesBefore.length - 1].length + 1;

        const selectionLines = selectedText.split('\n');

        endLine = startLine + selectionLines.length - 1;

        if (selectionLines.length === 1) {
          endColumn = startColumn + selectedText.length - 1;
        } else {
          endColumn = selectionLines[selectionLines.length - 1].length + 1;
        }
      }
    }

    const newSelection = {
      id: Date.now(),
      code: selectedText,
      startLine,
      startColumn,
      endLine,
      endColumn,
      time: new Date().toLocaleTimeString(),
    };

    // Get position of selected text
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Show popup near selected text
    setSelectionPopup({
      ...newSelection,
      top: rect.bottom + window.scrollY + 8,
      left: rect.left + window.scrollX,
    });

    // Clear previous explanation
    setExplanation('');
    setExplanationError('');
  };

  const handleExplainCode = async () => {
    if (!selectionPopup) return;

    // Abort any existing pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setExplanationLoading(true);
    setExplanationError('');
    setExplanation('');

    try {
      const response = await axios.post(
        'http://localhost:8000/response',
        {
          code: selectionPopup.code,
          startLine: selectionPopup.startLine,
          startColumn: selectionPopup.startColumn,        
          endLine: selectionPopup.endLine,
          endColumn: selectionPopup.endColumn,
        },
        {
          signal: controller.signal,
        }
      );

      // Check if cancelled
      if (controller.signal.aborted) return;

      console.log('Explanation response:', response.data);

      setExplanation(
        response.data.explanation ||
        response.data.response ||
        response.data.message ||
        'No explanation returned.'
      );

    } catch (err) {
      if (axios.isCancel(err) || err.name === 'CanceledError' || err.name === 'AbortError') {
        console.log('Explanation request cancelled by user.');
        return;
      }

      console.error('Explanation Error:', err);

      setExplanationError(
        err.response?.data?.message ||
        'Failed to get explanation from the backend.'
      );
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        setExplanationLoading(false);
      }
    }
  };

  const closeSelectionPopup = () => {
    cancelExplanationRequest();
    setSelectionPopup(null);
  };


  return (
    <>
      <div className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <span className="logo-mark">R</span>
            <span className="wordmark">RETRIEVR</span>
          </div>
          <div className="topbar-meta">
            <button
              className="theme-toggle"
              onClick={() => setTheme(t => (t === 'light' ? 'dark' : 'light'))}
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
              aria-label="Toggle color theme"
            >
              <i className={theme === 'light' ? 'ti ti-moon-stars' : 'ti ti-sun'} />
              <span>{theme === 'light' ? 'dark' : 'light'}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="header">
          <div className="welcome-panel">
            <div className="welcome-grid">
              <div className="welcome-left">
                <p className="panel-label">Session</p>
                <div className="status-list">
                  <div className="status-row">
                    <dt>file</dt>
                    <dd className={filename ? 'status-file' : ''}>{filename || 'none'}</dd>
                  </div>
                  <div className="status-row">
                    <dt>chunks</dt>
                    <dd>{chunksCount ?? '—'}</dd>
                  </div>
                  <div className="status-row">
                    <dt>model</dt>
                    <dd>gemini-3.1-flash-lite</dd>
                  </div>
                  <div className="status-row">
                    <dt>path</dt>
                    <dd>~/retrievr</dd>
                  </div>
                </div>
              </div>
              <div className="welcome-right">
                <div className="tip-block">
                  <p className="tip-title">Tips for getting started</p>
                  <p className="tip-body">Upload a file, then select any code to capture and explain it</p>
                </div>
                <div className="tip-block">
                  <p className="tip-title">Recent activity</p>
                  <p className={`tip-body${filename ? '' : ' dim'}`}>
                    {filename
                      ? `Indexed ${filename} · ${fileContent.split('\n').length} lines`
                      : 'No recent activity'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="prompt-line">
            <span className="prompt-caret">❯</span>
            <span className="prompt-text">{filename ? `read ${filename}` : 'upload a file'}</span>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            <span><i className="ti ti-alert-triangle" /> {error}</span>
            <button className="action-btn" onClick={() => setError('')}>Dismiss</button>
          </div>
        )}

        {!fileContent ? (
          <div className="card">
            <div 
              className={`upload-box ${isDragging ? 'dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput').click()}
            >
              <input 
                type="file" 
                id="fileInput" 
                className="file-input" 
                onChange={handleFileChange}
              />
              <span className="upload-icon"><i className="ti ti-file-upload" /></span>
              <h3>{selectedFile ? selectedFile.name : 'Click or drag & drop a file here'}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: '0.5rem' }}>
                Supports code files, text files, markdown, python, etc.
              </p>
            </div>

            {selectedFile && (
              <div className="file-info">
                <div>
                  Selected: <span className="file-name">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
                <button 
                  className="upload-btn" 
                  onClick={handleUpload} 
                  disabled={loading}
                >
                  {loading ? <><span className="loader"></span> Processing...</> : <>Upload &amp; view <i className="ti ti-arrow-right" /></>}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="layout-grid">
            {/* Main Code & Text Viewer */}
            <div className="card viewer-card">
              <div className="viewer-header">
                <div className="viewer-title-group">
                  <div className="tool-line">
                    <span className="tool-dot">●</span>
                    <span className="tool-name">Read</span>
                    <span className="tool-args">({filename})</span>
                  </div>
                  <div className="tool-meta">
                    └ {chunksCount !== null && (
                      <>
                        {chunksCount} chunks in Qdrant
                        <span className="sep">·</span>
                      </>
                    )}
                    {fileContent.split('\n').length} lines
                    <span className="sep">·</span>
                    {fileContent.length} chars
                  </div>
                </div>

                <div className="viewer-actions">
                  <button className="action-btn" onClick={() => { setFileContent(''); setSelectedFile(null); }}>
                    <i className="ti ti-folder" /> Change file
                  </button>
                  <button className="action-btn" onClick={handleCopy}>
                    {copied ? <><i className="ti ti-check" /> Copied</> : <><i className="ti ti-copy" /> Copy all</>}
                  </button>
                </div>
              </div>

              {/* Dynamic Viewer Toolbar */}
              <div className="viewer-toolbar">
                <div className="search-box">
                  <span className="search-icon"><i className="ti ti-search" /></span>
                  <input 
                    type="text" 
                    placeholder="Search in file..." 
                    value={searchTerm} 
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                  />
                  {searchTerm && (
                    <button className="clear-search-btn" onClick={() => setSearchTerm('')}>×</button>
                  )}
                </div>

                <div className="toolbar-controls">
                  <button 
                    className={`action-btn ${isWrapped ? 'active-btn' : ''}`} 
                    onClick={() => setIsWrapped(!isWrapped)}
                    title="Toggle Word Wrap"
                  >
                    {isWrapped ? <><i className="ti ti-wrap" /> Wrap: on</> : <><i className="ti ti-arrows-horizontal" /> Wrap: off</>}
                  </button>

                  <div className="font-controls">
                    <span className="font-label">font</span>
                    <button 
                      className="action-btn font-btn" 
                      onClick={() => setFontSize(prev => Math.max(10, prev - 1))}
                      title="Decrease Font Size"
                    >
                      A-
                    </button>
                    <span className="font-size-val">{fontSize}px</span>
                    <button 
                      className="action-btn font-btn" 
                      onClick={() => setFontSize(prev => Math.min(24, prev + 1))}
                      title="Increase Font Size"
                    >
                      A+
                    </button>
                  </div>
                </div>
              </div>

              <div 
                className={`code-container ${isWrapped ? 'wrapped' : 'nowrap'}`} 
                style={{ fontSize: `${fontSize}px` }}
                onMouseUp={handleMouseUp} 
                onKeyUp={handleMouseUp}
              >
                <div className="code-viewer-table">
                  {fileContent.split('\n').map((line, idx) => {
                    const lineNum = idx + 1;
                    const isHighlighted = searchTerm.trim() !== '' && line.toLowerCase().includes(searchTerm.toLowerCase());
                    return (
                      <div key={idx} className={`code-line ${isHighlighted ? 'highlighted-line' : ''}`}>
                        <span className="line-number">{lineNum}</span>
                        <span className="line-content">{renderLine(line)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <footer className="footer">
        <div className="footer-bottom">
          <span>RETRIEVR · code-aware RAG</span>
          <span>FastAPI · tree-sitter · sentence-transformers · Qdrant · Gemini</span>
        </div>
      </footer>

      {selectionPopup && (
          <div
            className="selection-popup"
            onMouseDown={(e) => e.preventDefault()}
            style={{
              position: 'absolute',
              top: selectionPopup.top,
              left: selectionPopup.left,
            }}
          >
            <button
              onClick={handleExplainCode}
              className="explain-button"
              disabled={explanationLoading}
            >
              {explanationLoading
                ? <><span className="loader"></span> Explaining...</>
                : <><span className="prompt-caret">❯</span> Explain code</>}
            </button>

            <button
              onClick={closeSelectionPopup}
              className="close-popup-button"
            >
              ×
            </button>
          </div>
        )}

      {explanation && (
        <div className="explanation-overlay">
          <div className="explanation-modal">

            <div className="explanation-header">
              <h2>Explain code</h2>

              <button
                onClick={() => setExplanation('')}
                className="modal-close"
              >
                ×
              </button>
            </div>

            <div className="selected-code">
              <pre>{selectionPopup?.code}</pre>
            </div>

            <div className="explanation-content">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>

          </div>
        </div>
      )}  
    </>
  );
}

export default App;

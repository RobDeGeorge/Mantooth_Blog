// blog-admin-interface.js - Enhanced admin interface with PDF selection
class BlogAdminInterface {
    constructor() {
        this.console = null;
        this.processing = false;
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.availablePDFs = [];
        this.init();
    }

    init() {
        this.console = document.getElementById('console-output');
        this.bindEvents();
        this.loadAvailablePDFs();
        this.log('Blog Admin Interface initialized', 'success');
    }

    bindEvents() {
        const processBtn = document.getElementById('process-blogs');
        const clearBtn = document.getElementById('clear-console');
        const refreshBtn = document.getElementById('refresh-pdfs');

        if (processBtn) {
            processBtn.addEventListener('click', () => {
                this.showPDFSelector();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.console.innerHTML = '';
                this.log('Console cleared', 'info');
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadAvailablePDFs();
            });
        }
    }

    log(message, type = 'info') {
        const colors = { 
            info: '#00ff00', 
            error: '#ff4444', 
            warning: '#ffaa00', 
            success: '#44ff44', 
            debug: '#88ccff' 
        };
        
        const logEntry = document.createElement('div');
        logEntry.style.color = colors[type] || colors.info;
        logEntry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
        this.console.appendChild(logEntry);
        this.console.scrollTop = this.console.scrollHeight;
    }

    async loadAvailablePDFs() {
        try {
            this.log('📂 Loading available PDF files...', 'info');
            
            const response = await fetch(`${this.apiBaseUrl}/list-pdfs`);
            const result = await response.json();
            
            if (result.success) {
                this.availablePDFs = result.pdfs;
                this.log(`✅ Found ${result.count} PDF files`, 'success');
                this.updatePDFDisplay();
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.log(`❌ Error loading PDFs: ${error.message}`, 'error');
            this.log('💡 Make sure the Python API is running: python web_api.py', 'info');
        }
    }

    updatePDFDisplay() {
        const container = document.getElementById('pdf-list-container');
        if (!container) return;

        if (this.availablePDFs.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    📂 No PDF files found in Raw Blogs folder<br>
                    Add PDF files to: assests/Blogs/Raw Blogs/
                </div>
            `;
            return;
        }

        const pdfHTML = this.availablePDFs.map(pdf => `
            <div class="pdf-item" style="background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 10px 0; cursor: pointer; transition: all 0.3s ease;" 
                 onclick="blogAdmin.selectPDF('${pdf.name}')" 
                 onmouseover="this.style.borderColor='#F18F01'" 
                 onmouseout="this.style.borderColor='#dee2e6'">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #2D4059;">${pdf.name}</h4>
                        <small style="color: #666;">
                            📊 ${pdf.size_mb} MB | 
                            📅 ${new Date(pdf.modified * 1000).toLocaleDateString()}
                        </small>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button onclick="event.stopPropagation(); blogAdmin.previewPDF('${pdf.name}')" 
                                style="background: #6c757d; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                            👁️ Preview
                        </button>
                        <button onclick="event.stopPropagation(); blogAdmin.processPDF('${pdf.name}')" 
                                style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                            🚀 Process
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = pdfHTML;
    }

    showPDFSelector() {
        if (this.availablePDFs.length === 0) {
            this.log('❌ No PDF files available. Add files to Raw Blogs folder.', 'error');
            return;
        }

        this.log('📋 Select a PDF file to process', 'info');
        // The PDF display is already shown, just scroll to it
        document.getElementById('pdf-list-container').scrollIntoView({ behavior: 'smooth' });
    }

    async previewPDF(pdfName) {
        try {
            this.log(`👁️ Previewing ${pdfName}...`, 'info');
            
            const response = await fetch(`${this.apiBaseUrl}/preview-pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pdf_name: pdfName })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showPreviewModal(result.preview);
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.log(`❌ Preview error: ${error.message}`, 'error');
        }
    }

    showPreviewModal(preview) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.8); z-index: 1000; display: flex; 
            align-items: center; justify-content: center; padding: 20px;
        `;
        
        modal.innerHTML = `
            <div style="background: white; border-radius: 12px; padding: 30px; max-width: 800px; max-height: 80vh; overflow-y: auto; position: relative;">
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="position: absolute; top: 10px; right: 15px; background: none; border: none; font-size: 24px; cursor: pointer;">×</button>
                
                <h2 style="color: #2D4059; margin-bottom: 20px;">📋 Blog Preview</h2>
                
                <div style="margin-bottom: 15px;">
                    <strong>Title:</strong> ${preview.title}<br>
                    <strong>Slug:</strong> ${preview.slug}<br>
                    <strong>Tags:</strong> ${preview.tags.join(', ')}<br>
                    <strong>Image:</strong> ${preview.featured_image}<br>
                    <strong>Pages:</strong> ${preview.total_pages} | <strong>Characters:</strong> ${preview.total_chars}<br>
                    <strong>Links Found:</strong> ${preview.links_found}
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>Excerpt:</strong>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 5px;">
                        ${preview.excerpt}
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <strong>Content Preview:</strong>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 5px; max-height: 200px; overflow-y: auto;">
                        ${preview.content_preview.replace(/<[^>]+>/g, '')}
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="blogAdmin.processPDF('${preview.slug.replace('-blog', '')}.pdf'); this.parentElement.parentElement.parentElement.remove();" 
                            style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                        🚀 Generate Blog
                    </button>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            style="background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    async processPDF(pdfName) {
        if (this.processing) return;
        
        this.processing = true;
        this.log(`🚀 Processing ${pdfName}...`, 'info');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/process-pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pdf_name: pdfName })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.log(`✅ Successfully processed ${pdfName}!`, 'success');
                this.log('📄 Blog generated and saved', 'success');
                this.log('📝 blogs.html updated', 'success');
                this.log('📊 JSON data updated', 'success');
                this.showSuccessResult(pdfName);
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.log(`❌ Processing error: ${error.message}`, 'error');
        } finally {
            this.processing = false;
        }
    }

    showSuccessResult(pdfName) {
        const resultsArea = document.getElementById('results-area');
        const resultsContent = document.getElementById('results-content');
        
        if (resultsArea && resultsContent) {
            resultsContent.innerHTML = `
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px;">
                    <h4 style="color: #155724; margin-bottom: 15px;">✅ Blog Generated Successfully!</h4>
                    <p><strong>Source:</strong> ${pdfName}</p>
                    <p><strong>Status:</strong> Blog created and website updated</p>
                    <div style="margin-top: 15px;">
                        <a href="blogs.html" target="_blank" style="background: #28a745; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                            View Updated Blogs
                        </a>
                        <button onclick="blogAdmin.loadAvailablePDFs()" style="background: #6c757d; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
                            Process Another PDF
                        </button>
                    </div>
                </div>
            `;
            resultsArea.style.display = 'block';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.blogAdmin = new BlogAdminInterface();
});
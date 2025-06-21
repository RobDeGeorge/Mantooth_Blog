// pdf-blog-processor.js - Real PDF text extraction, no demos
class PDFBlogProcessor {
    constructor() {
        this.console = null;
        this.pendingBlogs = [];
        this.init();
    }

    init() {
        this.createDebugConsole();
        this.bindProcessingEvents();
        window.pdfProcessor = this;
        this.log('PDF Processor initialized - Real PDF extraction mode', 'success');
        
        // Check if PDF.js is loaded
        if (typeof pdfjsLib !== 'undefined') {
            this.log('PDF.js library loaded successfully', 'success');
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        } else {
            this.log('ERROR: PDF.js library not found!', 'error');
        }
    }

    createDebugConsole() {
        const consoleHTML = `
            <div id="debug-console" style="background: #1a1a1a; color: #00ff00; font-family: monospace; padding: 15px; border-radius: 8px; margin: 20px 0; height: 200px; overflow-y: auto; font-size: 0.9em;">
                <div style="border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px;">
                    🖥️ Debug Console - Real PDF Extraction
                    <button id="clear-console" style="float: right; background: #333; color: #00ff00; border: 1px solid #555; padding: 2px 8px; cursor: pointer;">Clear</button>
                </div>
                <div id="console-output"></div>
            </div>
        `;

        document.querySelector('.admin-container').insertAdjacentHTML('beforeend', consoleHTML);
        this.console = document.getElementById('console-output');
        
        document.getElementById('clear-console').addEventListener('click', () => {
            this.console.innerHTML = '';
            this.log('Console cleared', 'info');
        });
    }

    log(message, type = 'info') {
        if (!this.console) return;
        const colors = { info: '#00ff00', error: '#ff4444', warning: '#ffaa00', success: '#44ff44', debug: '#88ccff' };
        const logEntry = document.createElement('div');
        logEntry.style.color = colors[type] || colors.info;
        logEntry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
        this.console.appendChild(logEntry);
        this.console.scrollTop = this.console.scrollHeight;
        console.log(`[PDF Processor] ${message}`);
    }

    bindProcessingEvents() {
        const processBtn = document.getElementById('process-pdfs');
        const fileInput = document.getElementById('pdf-upload');
        
        processBtn.addEventListener('click', () => {
            const files = fileInput.files;
            if (files.length > 0) {
                this.log(`Processing ${files.length} PDF file(s)`, 'info');
                this.processPDFFiles(files);
            } else {
                alert('Please select PDF files to process');
            }
        });

        fileInput.addEventListener('change', (e) => {
            this.log(`${e.target.files.length} file(s) selected`, 'info');
        });
    }

    async processPDFFiles(files) {
        document.getElementById('processing-results').innerHTML = '';
        document.getElementById('deployment-controls').style.display = 'none';
        this.pendingBlogs = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                this.log(`Extracting text from ${file.name}...`, 'info');
                const blogData = await this.extractBlogDataFromPDF(file);
                const generatedBlog = await this.generateBlogFromData(blogData);
                
                const blogEntry = {
                    fileName: file.name,
                    blogData: blogData,
                    generatedBlog: generatedBlog,
                    id: `blog-${Date.now()}-${i}`
                };
                
                this.pendingBlogs.push(blogEntry);
                this.displayEditableBlogPreview(blogEntry, document.getElementById('processing-results'));
                this.log(`✅ Successfully extracted ${blogData.content.length} characters from ${file.name}`, 'success');
                
            } catch (error) {
                this.log(`❌ Error processing ${file.name}: ${error.message}`, 'error');
                this.displayError(file.name, error.message, document.getElementById('processing-results'));
            }
        }
        
        if (this.pendingBlogs.length > 0) {
            this.createDeploymentControls();
        }
    }

    async extractBlogDataFromPDF(file) {
        this.log(`Reading PDF file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'debug');
        
        if (typeof pdfjsLib === 'undefined') {
            throw new Error('PDF.js library not loaded. Please refresh the page.');
        }

        try {
            // Read the PDF file as array buffer
            const arrayBuffer = await this.fileToArrayBuffer(file);
            this.log('PDF file loaded as array buffer', 'debug');
            
            // Load PDF document
            const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
            this.log(`PDF loaded: ${pdf.numPages} pages`, 'debug');
            
            // Extract text from all pages
            let fullText = '';
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                this.log(`Extracting text from page ${pageNum}/${pdf.numPages}`, 'debug');
                const page = await pdf.getPage(pageNum);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map(item => item.str).join(' ');
                fullText += pageText + '\n\n';
            }
            
            this.log(`Extracted ${fullText.length} characters of text`, 'debug');
            
            if (fullText.trim().length === 0) {
                throw new Error('No text content found in PDF. The PDF might be image-based or corrupted.');
            }
            
            // Process the extracted text
            const title = this.extractTitleFromFilename(file.name);
            const cleanedText = this.cleanExtractedText(fullText);
            const formattedContent = this.formatContent(cleanedText);
            const excerpt = this.generateExcerpt(cleanedText);
            const suggestedTags = this.suggestTags(cleanedText);
            const imageName = this.generateImageName(file.name);
            
            this.log(`Generated title: "${title}"`, 'debug');
            this.log(`Content length: ${formattedContent.length} characters`, 'debug');
            this.log(`Suggested tags: ${suggestedTags.join(', ')}`, 'debug');
            
            return {
                title: title,
                content: formattedContent,
                excerpt: excerpt,
                tags: suggestedTags,
                featuredImage: imageName,
                publishDate: new Date().toISOString().split('T')[0],
                fileName: file.name
            };
            
        } catch (error) {
            this.log(`PDF extraction failed: ${error.message}`, 'error');
            throw new Error(`Failed to extract text from PDF: ${error.message}`);
        }
    }

    fileToArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsArrayBuffer(file);
        });
    }

    cleanExtractedText(rawText) {
        this.log('Cleaning extracted text...', 'debug');
        
        // Remove excessive whitespace and clean up text
        let cleaned = rawText
            .replace(/\s+/g, ' ')  // Replace multiple spaces with single space
            .replace(/\n\s*\n/g, '\n\n')  // Clean up paragraph breaks
            .replace(/^\s+|\s+$/g, '')  // Trim whitespace
            .replace(/([.!?])\s*([A-Z])/g, '$1\n\n$2');  // Add paragraph breaks after sentences
        
        // Remove common PDF artifacts
        cleaned = cleaned
            .replace(/\f/g, '\n\n')  // Form feed to paragraph break
            .replace(/Page \d+/gi, '')  // Remove page numbers
            .replace(/\d{1,3}\s*$/gm, '')  // Remove trailing page numbers
            .replace(/^\d+\s+/gm, '');  // Remove leading numbers
        
        this.log(`Text cleaned: ${cleaned.length} characters`, 'debug');
        return cleaned;
    }

    extractTitleFromFilename(fileName) {
        let title = fileName.replace('.pdf', '').replace(/[_-]/g, ' ');
        return title.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
    }

    formatContent(cleanedText) {
        this.log('Formatting content to HTML...', 'debug');
        
        // Split into paragraphs
        const paragraphs = cleanedText.split('\n\n').filter(p => p.trim().length > 10);
        
        // Convert to HTML paragraphs
        const htmlContent = paragraphs.map(paragraph => {
            const trimmed = paragraph.trim();
            return `<p>${trimmed}</p>`;
        }).join('\n\n                    ');
        
        this.log(`Formatted ${paragraphs.length} paragraphs to HTML`, 'debug');
        return htmlContent;
    }

    generateExcerpt(content) {
        this.log('Generating excerpt...', 'debug');
        
        // Find the first substantial paragraph for excerpt
        const paragraphs = content.split('\n\n').filter(p => p.trim().length > 50);
        
        if (paragraphs.length > 0) {
            const firstParagraph = paragraphs[0].trim();
            const excerpt = firstParagraph.length > 200 ? 
                firstParagraph.substring(0, 197) + '...' : firstParagraph;
            this.log(`Generated excerpt: "${excerpt.substring(0, 50)}..."`, 'debug');
            return excerpt;
        }
        
        // Fallback
        const excerpt = content.substring(0, 200) + '...';
        this.log(`Generated fallback excerpt`, 'debug');
        return excerpt;
    }

    suggestTags(content) {
        this.log('Analyzing content for tag suggestions...', 'debug');
        
        const contentLower = content.toLowerCase();
        const tags = [];
        
        // Location-based tags
        const locations = [
            { keywords: ['phoenix', 'arizona', 'az'], tag: 'phoenix' },
            { keywords: ['gatlinburg', 'tennessee', 'tn'], tag: 'gatlinburg' },
            { keywords: ['los angeles', 'la', 'california'], tag: 'los angeles' },
            { keywords: ['new york', 'nyc', 'manhattan'], tag: 'new york' }
        ];
        
        locations.forEach(location => {
            if (location.keywords.some(keyword => contentLower.includes(keyword))) {
                tags.push(location.tag);
            }
        });
        
        // Activity-based tags
        const activities = [
            { keywords: ['restaurant', 'food', 'eat', 'dining', 'meal'], tags: ['food', 'restaurants'] },
            { keywords: ['cocktail', 'drink', 'bar', 'alcohol'], tags: ['cocktails'] },
            { keywords: ['music', 'concert', 'band', 'performance'], tags: ['music', 'concerts'] },
            { keywords: ['travel', 'trip', 'vacation', 'journey'], tags: ['travel'] },
            { keywords: ['hike', 'hiking', 'trail', 'mountain'], tags: ['hiking', 'outdoors'] },
            { keywords: ['festival', 'event', 'celebration'], tags: ['events'] },
            { keywords: ['cat', 'pet', 'animal'], tags: ['pets'] },
            { keywords: ['review', 'opinion'], tags: ['reviews'] }
        ];
        
        activities.forEach(activity => {
            if (activity.keywords.some(keyword => contentLower.includes(keyword))) {
                tags.push(...activity.tags);
            }
        });
        
        // Always add lifestyle
        tags.push('lifestyle');
        
        // Remove duplicates and limit to 6 tags
        const uniqueTags = [...new Set(tags)].slice(0, 6);
        this.log(`Generated ${uniqueTags.length} tags: ${uniqueTags.join(', ')}`, 'debug');
        
        return uniqueTags;
    }

    generateImageName(fileName) {
        return fileName.replace('.pdf', '').toLowerCase()
            .replace(/[^a-z0-9]/g, '_')
            .replace(/_+/g, '_')
            .trim('_') + '_blog.png';
    }

    async generateBlogFromData(blogData) {
        this.log('Generating blog HTML files...', 'debug');
        
        try {
            const generator = new BlogGenerator();
            const blog = generator.addBlogPost(blogData);
            
            return {
                blogHTML: generator.generateBlogFiles(blog),
                blogItem: generator.generateBlogItemHTML(blog),
                slug: blog.slug,
                imageName: blogData.featuredImage,
                blogData: blogData
            };
        } catch (error) {
            this.log(`Error generating blog: ${error.message}`, 'error');
            throw error;
        }
    }

    displayEditableBlogPreview(blogEntry, container) {
        const { fileName, blogData, id } = blogEntry;
        
        const previewHTML = `
            <div class="blog-preview" data-blog-id="${id}" style="background: #f8f9fa; border: 2px solid #28a745; border-radius: 8px; padding: 20px; margin: 15px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h5 style="color: #28a745; margin: 0;">📄 ${fileName} (${blogData.content.length} chars)</h5>
                    <span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">Ready</span>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; font-weight: bold; margin-bottom: 5px;">📝 Title:</label>
                    <input type="text" class="title-editor" data-blog-id="${id}" value="${blogData.title}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; font-weight: bold; margin-bottom: 5px;">🏷️ Tags:</label>
                    <div class="tag-editor" data-blog-id="${id}" style="display: flex; flex-wrap: wrap; gap: 5px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; min-height: 40px;">
                        ${blogData.tags.map(tag => `
                            <span style="background: #F18F01; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.9em;">
                                ${tag} <button onclick="this.parentElement.remove(); window.pdfProcessor.updateBlogData('${id}');" style="background: none; border: none; color: white; margin-left: 4px; cursor: pointer;">×</button>
                            </span>
                        `).join('')}
                        <input type="text" placeholder="Add tag..." style="border: none; outline: none; min-width: 80px;" onkeypress="if(event.key==='Enter'||event.key===','){window.pdfProcessor.addTag(this, '${id}'); event.preventDefault();}">
                    </div>
                </div>
                
                <div style="background: white; padding: 10px; border-radius: 4px; margin: 10px 0;">
                    <strong>Content Preview:</strong>
                    <div style="max-height: 150px; overflow-y: auto; margin-top: 5px; font-size: 0.9em; line-height: 1.4;">${blogData.excerpt}</div>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', previewHTML);
        
        // Bind title editing
        container.querySelector(`.title-editor[data-blog-id="${id}"]`).addEventListener('input', (e) => {
            this.updateBlogTitle(id, e.target.value);
        });
    }

    displayError(fileName, error, container) {
        const errorHTML = `
            <div style="background: #f8d7da; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #dc3545;">
                <h5>❌ Error: ${fileName}</h5>
                <p style="color: #721c24;">${error}</p>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', errorHTML);
    }

    addTag(inputElement, blogId) {
        const tagText = inputElement.value.trim().replace(',', '');
        if (!tagText) return;
        
        const tagElement = document.createElement('span');
        tagElement.style.cssText = 'background: #F18F01; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.9em;';
        tagElement.innerHTML = `${tagText} <button onclick="this.parentElement.remove(); window.pdfProcessor.updateBlogData('${blogId}');" style="background: none; border: none; color: white; margin-left: 4px; cursor: pointer;">×</button>`;
        
        inputElement.parentElement.insertBefore(tagElement, inputElement);
        inputElement.value = '';
        this.updateBlogData(blogId);
    }

    updateBlogTitle(blogId, newTitle) {
        const blog = this.pendingBlogs.find(b => b.id === blogId);
        if (blog) {
            blog.blogData.title = newTitle;
            blog.generatedBlog.slug = this.createSlug(newTitle);
        }
    }

    updateBlogData(blogId) {
        const tagEditor = document.querySelector(`.tag-editor[data-blog-id="${blogId}"]`);
        const tagElements = tagEditor.querySelectorAll('span');
        const currentTags = Array.from(tagElements).map(el => el.textContent.trim().replace('×', ''));
        
        const blog = this.pendingBlogs.find(b => b.id === blogId);
        if (blog) {
            blog.blogData.tags = currentTags;
        }
    }

    createSlug(title) {
        return title.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-').trim('-') + '-blog';
    }

    createDeploymentControls() {
        const deploymentControls = document.getElementById('deployment-controls');
        deploymentControls.innerHTML = `
            <div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0 0 15px 0;">🚀 Deploy ${this.pendingBlogs.length} Blog Post${this.pendingBlogs.length > 1 ? 's' : ''}!</h4>
                <button id="deploy-all-blogs" style="background: white; color: #28a745; border: none; padding: 12px 25px; border-radius: 25px; font-weight: bold; cursor: pointer;">Deploy Now</button>
                <button id="cancel-deployment" style="background: rgba(255,255,255,0.2); color: white; border: 2px solid white; padding: 10px 20px; border-radius: 25px; cursor: pointer; margin-left: 10px;">Cancel</button>
            </div>
        `;
        deploymentControls.style.display = 'block';
        
        document.getElementById('deploy-all-blogs').addEventListener('click', () => {
            this.deployAllBlogs();
        });
        
        document.getElementById('cancel-deployment').addEventListener('click', () => {
            deploymentControls.style.display = 'none';
            this.pendingBlogs = [];
        });
    }

    async deployAllBlogs() {
        this.log('🚀 Starting deployment...', 'info');
        
        // Update all blog data from current state
        this.pendingBlogs.forEach(blog => {
            this.updateBlogData(blog.id);
            this.updateBlogTitle(blog.id, document.querySelector(`.title-editor[data-blog-id="${blog.id}"]`).value);
        });

        // Regenerate and download files
        for (let blog of this.pendingBlogs) {
            await this.regenerateAndDownload(blog);
        }
        
        this.log('✅ Deployment complete! Files downloaded.', 'success');
    }

    async regenerateAndDownload(blog) {
        // Regenerate with updated data
        const generator = new BlogGenerator();
        const updatedBlog = generator.addBlogPost(blog.blogData);
        
        // Download individual blog file
        const blogHTML = generator.generateBlogFiles(updatedBlog);
        this.downloadFile(`${updatedBlog.slug}.html`, blogHTML);
        
        this.log(`📥 Downloaded: ${updatedBlog.slug}.html`, 'info');
    }

    downloadFile(fileName, content) {
        const blob = new Blob([content], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        link.click();
        URL.revokeObjectURL(url);
    }
}
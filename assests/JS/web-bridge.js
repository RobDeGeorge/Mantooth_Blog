// web-bridge.js - Bridge between frontend and Python backend
class WebBridge {
    constructor() {
        this.apiBaseUrl = 'http://localhost:3001/api';
        this.logger = null;
        this.checkConnection();
    }

    setLogger(loggerFunction) {
        this.logger = loggerFunction;
    }

    log(message, type = 'info') {
        if (this.logger) {
            this.logger(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                const data = await response.json();
                this.log(`✅ Connected to ${data.service}`, 'success');
                return true;
            } else {
                throw new Error('Service not responding');
            }
        } catch (error) {
            this.log('⚠️ Python processing service not running', 'warning');
            this.log('To start service: cd python && npm start', 'info');
            return false;
        }
    }

    async processPDFs(config = {}) {
        this.log('📡 Sending processing request to Python backend...', 'info');

        try {
            const response = await fetch(`${this.apiBaseUrl}/process-blogs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'process_pdfs',
                    config: config,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                this.log('✅ Python processing completed successfully!', 'success');
                
                // Parse and display Python output
                if (result.output) {
                    this.displayPythonOutput(result.output);
                }

                if (result.warnings) {
                    this.log(`⚠️ Warnings: ${result.warnings}`, 'warning');
                }

                // Save processing results to JSON
                await this.saveProcessingResults(result);
                
                return result;
                
            } else {
                throw new Error(result.error || 'Unknown processing error');
            }
            
        } catch (error) {
            if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
                throw new Error('Could not connect to Python service. Make sure it\'s running with: cd python && npm start');
            } else {
                throw error;
            }
        }
    }

    displayPythonOutput(output) {
        const lines = output.split('\n');
        lines.forEach(line => {
            const trimmedLine = line.trim();
            if (trimmedLine) {
                if (trimmedLine.includes('ERROR')) {
                    this.log(trimmedLine, 'error');
                } else if (trimmedLine.includes('Created:') || trimmedLine.includes('Successfully') || trimmedLine.includes('✅')) {
                    this.log(trimmedLine, 'success');
                } else if (trimmedLine.includes('WARNING') || trimmedLine.includes('⚠️')) {
                    this.log(trimmedLine, 'warning');
                } else {
                    this.log(trimmedLine, 'info');
                }
            }
        });
    }

    async saveProcessingResults(result) {
        // Save processing results to local storage for reference
        const processingLog = {
            timestamp: new Date().toISOString(),
            success: result.success,
            output: result.output,
            warnings: result.warnings,
            filesGenerated: this.extractGeneratedFiles(result.output)
        };

        localStorage.setItem('last-processing-result', JSON.stringify(processingLog));
        this.log('💾 Processing results saved to browser storage', 'debug');
    }

    extractGeneratedFiles(output) {
        const files = [];
        const lines = output.split('\n');
        
        lines.forEach(line => {
            if (line.includes('Created:')) {
                const filePath = line.split('Created:')[1]?.trim();
                if (filePath) {
                    files.push(filePath);
                }
            }
        });
        
        return files;
    }

    async getLastProcessingResult() {
        const stored = localStorage.getItem('last-processing-result');
        return stored ? JSON.parse(stored) : null;
    }

    async validateFiles() {
        this.log('🔍 Validating generated files...', 'info');
        
        const lastResult = await this.getLastProcessingResult();
        if (!lastResult) {
            this.log('No previous processing results found', 'warning');
            return false;
        }

        // Here you could add file validation logic
        this.log(`Last processing: ${lastResult.timestamp}`, 'debug');
        this.log(`Files generated: ${lastResult.filesGenerated.length}`, 'debug');
        
        return true;
    }
}

// Make WebBridge globally available
window.WebBridge = WebBridge;
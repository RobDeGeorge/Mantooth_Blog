const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

class BlogProcessorBridge {
    constructor() {
        this.pythonScript = path.join(__dirname, '..', 'blog-processor', 'src', 'main.py');
        this.projectRoot = path.dirname(path.dirname(__dirname));
    }

    async processPDFs() {
        return new Promise((resolve, reject) => {
            console.log('🚀 Starting Python blog processor...');
            
            // Check if Python script exists
            if (!fs.existsSync(this.pythonScript)) {
                reject(new Error(`Python script not found: ${this.pythonScript}`));
                return;
            }

            // Execute Python script
            const pythonCommand = `python3 "${this.pythonScript}"`;
            
            exec(pythonCommand, { cwd: this.projectRoot }, (error, stdout, stderr) => {
                if (error) {
                    console.error('❌ Python execution error:', error);
                    reject(error);
                    return;
                }

                if (stderr) {
                    console.warn('⚠️ Python warnings:', stderr);
                }

                console.log('✅ Python output:');
                console.log(stdout);
                
                resolve({
                    success: true,
                    output: stdout,
                    warnings: stderr || null
                });
            });
        });
    }
}

// CLI usage
if (require.main === module) {
    const bridge = new BlogProcessorBridge();
    bridge.processPDFs()
        .then(result => {
            console.log('🎉 Blog processing completed successfully!');
            process.exit(0);
        })
        .catch(error => {
            console.error('💥 Blog processing failed:', error.message);
            process.exit(1);
        });
}

module.exports = BlogProcessorBridge;
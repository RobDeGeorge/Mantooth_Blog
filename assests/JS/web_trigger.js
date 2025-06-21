const express = require('express');
const cors = require('cors');
const BlogProcessorBridge = require('./run_blog_processor');

const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

// Bridge instance
const bridge = new BlogProcessorBridge();

// API endpoint to trigger blog processing
app.post('/api/process-blogs', async (req, res) => {
    try {
        console.log('📡 Received blog processing request from web interface');
        
        const result = await bridge.processPDFs();
        
        res.json({
            success: true,
            message: 'Blog processing completed successfully',
            output: result.output,
            warnings: result.warnings
        });
        
    } catch (error) {
        console.error('❌ Processing error:', error);
        
        res.status(500).json({
            success: false,
            error: error.message,
            message: 'Blog processing failed'
        });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', service: 'Mantooth Blog Processor' });
});

// Start server
app.listen(port, () => {
    console.log(`🦷 Mantooth Blog Processor API running on http://localhost:${port}`);
    console.log('Ready to process PDF blogs!');
});
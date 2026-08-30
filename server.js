const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json({ limit: '10mb' }));

app.post('/ocr', (req, res) => {
    const { imageBase64 } = req.body;

    if (!imageBase64) {
        return res.status(400).json({ error: 'No image data provided' });
    }

    // Base64 image ko file me convert karke temp folder me save karna
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const tempFileName = `temp_${Date.now()}.png`;
    const tempPath = path.join(__dirname, tempFileName);

    fs.writeFileSync(tempPath, base64Data, 'base64');

    // Python script ko spawn karke execute karna
    const pythonProcess = spawn('py', ['capcha_ocr_local.py', tempPath]);

    let output = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        // Cleaning temporary file
        if (fs.existsSync(tempPath)) {
            fs.unlinkSync(tempPath);
        }

        // Output regex filtering
        const match = output.match(/OCR RESULT\s*:\s*(.*)/);
        const resultText = match ? match[1].trim() : '';

        res.json({
            success: true,
            text: resultText === '(nothing detected)' ? '' : resultText
        });
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`OCR Server live at http://localhost:${PORT}`);
});
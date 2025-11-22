const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

console.log('--- Checking Classifier Configuration ---');
const enableClassifier = process.env.ENABLE_CLASSIFIER;
console.log('ENABLE_CLASSIFIER env var:', enableClassifier);

const scriptPath = path.join(__dirname, 'src/Services/ai/email_classifier.py');
console.log('Python script path:', scriptPath);
console.log('Script exists:', fs.existsSync(scriptPath));

if (fs.existsSync(scriptPath)) {
    console.log('\n--- Testing Python Script Execution ---');
    const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
    const python = spawn(pythonBin, [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => { stdout += data.toString(); });
    python.stderr.on('data', (data) => { stderr += data.toString(); });

    python.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
        if (stdout) console.log('Python Output:', stdout.trim());
        if (stderr) console.error('Python Error:', stderr.trim());

        checkApi();
    });

    python.stdin.write("This is a test email to check classification.");
    python.stdin.end();
} else {
    checkApi();
}

async function checkApi() {
    console.log('\n--- Checking API Data ---');
    try {
        const response = await axios.get('http://localhost:3000/api/emails/search?q=a');
        if (response.data.results && response.data.results.length > 0) {
            const categories = response.data.results.map(e => e.aiCategory || e.category);
            console.log('Categories found in first 5 emails:', categories.slice(0, 5));
        } else {
            console.log('No emails found to check categories.');
        }
    } catch (error) {
        console.error('API Error:', error.message);
    }
}

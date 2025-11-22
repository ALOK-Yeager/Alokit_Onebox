const axios = require('axios');
const { spawn } = require('child_process');
const path = require('path');
const https = require('https');

const ES_URL = process.env.ELASTICSEARCH_URL || 'https://127.0.0.1:9200';
const INDEX_NAME = 'emails';
const PYTHON_SCRIPT = path.join(__dirname, 'src/Services/ai/email_classifier.py');
const AUTH = {
    username: process.env.ELASTICSEARCH_USERNAME || 'elastic',
    password: process.env.ELASTICSEARCH_PASSWORD || 'changeme'
};

const axiosInstance = axios.create({
    httpsAgent: new https.Agent({
        rejectUnauthorized: false
    }),
    auth: AUTH
});

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function classifyText(text) {
    return new Promise((resolve, reject) => {
        const pythonBin = process.platform === 'win32' ? 'python' : 'python3';
        const python = spawn(pythonBin, [PYTHON_SCRIPT], {
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => stdout += data.toString());
        python.stderr.on('data', (data) => stderr += data.toString());

        python.on('close', (code) => {
            if (code !== 0) {
                return resolve({ category: 'Unclassified', error: stderr || 'Unknown error' });
            }
            try {
                const result = JSON.parse(stdout.trim());
                resolve(result);
            } catch (e) {
                resolve({ category: 'Unclassified', error: 'Parse error' });
            }
        });

        python.stdin.write(text);
        python.stdin.end();
    });
}

async function reclassifyEmails() {
    try {
        console.log(`Fetching emails from Elasticsearch at ${ES_URL}...`);
        const response = await axiosInstance.get(`${ES_URL}/${INDEX_NAME}/_search?size=1000`);
        const hits = response.data.hits.hits;
        console.log(`Found ${hits.length} emails.`);

        for (const hit of hits) {
            const email = hit._source;
            const emailId = hit._id;

            const text = `${email.subject || ''}\n\n${email.body || ''}`.trim();
            if (text.length < 5) {
                console.log(`Skipping ${emailId}: Text too short.`);
                continue;
            }

            console.log(`Classifying email ${emailId}: ${email.subject?.substring(0, 30)}...`);
            const classification = await classifyText(text);

            if (classification.category && classification.category !== 'Unclassified') {
                console.log(` -> ${classification.category} (${classification.confidence})`);

                // Update Elasticsearch
                await axiosInstance.post(`${ES_URL}/${INDEX_NAME}/_update/${emailId}`, {
                    doc: {
                        aiCategory: classification.category,
                        aiConfidence: classification.confidence,
                        category: classification.category
                    }
                });
                console.log(' -> Updated in ES');
            } else {
                console.log(` -> Failed: ${classification.error}`);
            }
        }
        console.log('Done reclassifying.');

    } catch (error) {
        console.error('Error Message:', error.message);
        console.error('Error Code:', error.code);
        if (error.response) {
            console.error('Response Status:', error.response.status);
            console.error('Response Data:', JSON.stringify(error.response.data, null, 2));
        } else {
            console.error('Full Error:', error);
        }
    }
}

reclassifyEmails();

import { ElasticsearchService } from './src/Services/search/ElasticsearchService';
import { Email } from './src/Services/imap/Email';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const PYTHON_SCRIPT = path.resolve(process.cwd(), 'src/Services/ai/email_classifier.py');
const logFile = path.join(process.cwd(), 'reclassify.log');

const log = (msg: string) => {
    console.log(msg);
    fs.appendFileSync(logFile, msg + '\n');
};

async function classifyText(text: string): Promise<any> {
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
                resolve({ category: 'Unclassified', error: 'Parse error: ' + stdout });
            }
        });

        python.stdin.write(text);
        python.stdin.end();
    });
}

const reclassify = async () => {
    log('Starting reclassification...');
    log('Python script: ' + PYTHON_SCRIPT);

    const esService = new ElasticsearchService();

    // Wait for ES init
    await new Promise(resolve => setTimeout(resolve, 2000));

    try {
        // Access client directly to search
        const client = (esService as any).client;
        const allDocs = await client.search({
            index: 'emails',
            size: 1000,
            query: { match_all: {} }
        });

        const hits = allDocs.hits.hits;
        log(`Found ${hits.length} emails to process.`);

        for (const hit of hits) {
            const source = hit._source as any;
            const email: Email = {
                id: hit._id,
                ...source,
                date: new Date(source.date)
            };

            const text = `${email.subject || ''}\n\n${email.body || ''}`.trim();
            if (text.length < 5) {
                log(`Skipping ${email.id}: Text too short.`);
                continue;
            }

            log(`Classifying ${email.id}: ${email.subject?.substring(0, 30)}...`);
            const result = await classifyText(text);

            if (result.category && result.category !== 'Unclassified') {
                log(` -> ${result.category} (${result.confidence})`);

                email.aiCategory = result.category;
                email.aiConfidence = result.confidence;

                await esService.indexEmail(email);
                log(' -> Updated');
            } else {
                log(` -> Failed/Unclassified: ${result.error || result.category}`);
            }
        }

    } catch (error) {
        log('Error: ' + error);
    }
};

reclassify();

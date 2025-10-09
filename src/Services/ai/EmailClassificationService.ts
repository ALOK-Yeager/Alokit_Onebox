import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import logger from '../utils/Logger';

export interface ClassificationResult {
    category: string;
    confidence?: number;
    error?: string;
    status?: 'available' | 'unavailable';
}

export class EmailClassificationService {
    private readonly pythonScriptPath: string;
    private isAvailable: boolean = false;

    constructor() {
        // Resolve Python script from project root so it works in dev and prod
        // Note: process.cwd() points to repo root in dev and to /app in Docker
        this.pythonScriptPath = path.resolve(process.cwd(), 'src/Services/ai/email_classifier.py');
        logger.info(`Python script path: ${this.pythonScriptPath}`);
        logger.info(`Current directory: ${__dirname}`);
        this.checkPythonAvailability();
    }

    private async checkPythonAvailability(): Promise<void> {
        try {
            logger.info('Checking Python classifier availability...');

            // Use a real email for testing to ensure model is loaded
            const testEmail = "Hi there! I'd love to schedule a meeting with you next week to discuss the project.";
            const result = await this.runPythonScript(testEmail);

            if (result.error) {
                logger.warn('Python classifier error:', result.error);
                this.isAvailable = false;
                return;
            }

            if (result.category && result.confidence !== undefined) {
                this.isAvailable = true;
                logger.info('✅ Email classification service initialized successfully');
            } else {
                this.isAvailable = false;
                logger.warn('⚠️ Python classifier returned unexpected response:', result);
            }
        } catch (error) {
            logger.warn('⚠️ Email classification service unavailable:', error);
            this.isAvailable = false;
        }
    }

    public async classifyEmail(emailText: string): Promise<ClassificationResult> {
        if (!this.isAvailable) {
            return {
                category: 'Unclassified',
                error: 'Classification service unavailable'
            };
        }

        try {
            // Log the input text for analysis
            logger.info('📧 Classifying email:');
            logger.info('-------------------');
            logger.info(emailText);
            logger.info('-------------------');

            // Sanitize input to prevent injection
            const sanitizedText = emailText.replace(/[\r\n]+/g, ' ').trim();

            if (!sanitizedText || sanitizedText.length < 5) {
                return {
                    category: 'Unclassified',
                    error: 'Email text too short for classification'
                };
            }

            const result = await this.runPythonScript(sanitizedText);

            if (result.error) {
                logger.error('Classification error:', result.error);
                return {
                    category: 'Unclassified',
                    error: result.error
                };
            }

            const finalResult: ClassificationResult = {
                category: result.category || 'Unclassified'
            };

            if (result.confidence !== undefined) {
                finalResult.confidence = result.confidence;
            }

            return finalResult;

        } catch (error) {
            logger.error('Email classification failed:', error);
            return {
                category: 'Unclassified',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private runPythonScript(input: string): Promise<ClassificationResult> {
        return new Promise((resolve) => {
            // Check if Python script exists
            if (!fs.existsSync(this.pythonScriptPath)) {
                logger.error(`Python script not found at: ${this.pythonScriptPath}`);
                resolve({
                    category: 'Unclassified',
                    error: `Python script not found at: ${this.pythonScriptPath}`
                });
                return;
            }

            logger.debug('Running Python classifier script...');
            logger.debug(`Input text: ${input.length > 100 ? input.slice(0, 100) + '...' : input}`);

            // Use cross-platform Python executable (override with PYTHON_BIN if needed)
            const pythonBin = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3');
            const python = spawn(pythonBin, [this.pythonScriptPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1'
                }
            });

            let stdout = '';
            let stderr = '';

            python.stdout.on('data', (data) => {
                stdout += data.toString();
                logger.debug('Python stdout:', data.toString().trim());
            });

            python.stderr.on('data', (data) => {
                stderr += data.toString();
                logger.debug('Python stderr:', data.toString().trim());
            });

            python.on('close', (code) => {
                if (code !== 0) {
                    const errorMsg = `Python script exited with code ${code}: ${stderr}`;
                    logger.error(errorMsg);
                    resolve({
                        category: 'Unclassified',
                        error: errorMsg
                    });
                    return;
                }

                if (!stdout.trim()) {
                    logger.warn('No output from Python script');
                    resolve({
                        category: 'Unclassified',
                        error: 'No output from Python script'
                    });
                    return;
                }

                try {
                    const result = JSON.parse(stdout.trim());
                    logger.debug('Python classification result:', result);
                    resolve(result);
                } catch (error) {
                    const errorMsg = error instanceof Error
                        ? `Failed to parse Python output: ${error.message}`
                        : 'Failed to parse Python output';
                    logger.error(errorMsg);
                    resolve({
                        category: stdout.trim() || 'Unclassified',
                        error: errorMsg
                    });
                }
            });

            python.on('error', (error) => {
                const errorMsg = `Failed to spawn Python process: ${error.message}`;
                logger.error(errorMsg);
                resolve({
                    category: 'Unclassified',
                    error: errorMsg
                });
            });

            // Send input to Python script
            python.stdin.write(input);
            python.stdin.end();

            // Timeout after 60 seconds to allow for model loading and inference
            setTimeout(() => {
                logger.warn('Python script execution timed out');
                python.kill();
                resolve({
                    category: 'Unclassified',
                    error: 'Classification timeout'
                });
            }, 60000);
        });
    }

    public isServiceAvailable(): boolean {
        return this.isAvailable;
    }
}

// ES module export
export default EmailClassificationService;

// CommonJS export for compatibility
module.exports = { EmailClassificationService };

const axios = require('axios');

async function reclassifyAllEmails() {
    try {
        console.log('Starting email reclassification via API...');

        // First, get all emails  
        const searchResponse = await axios.get('http://localhost:3000/api/emails/search?q=a');
        const emails = searchResponse.data.results || searchResponse.data.emails || [];

        console.log(`Found ${emails.length} emails to process\n`);

        if (emails.length === 0) {
            console.log('No emails found. Make sure the backend is running and emails are indexed.');
            return;
        }

        let successCount = 0;
        let failCount = 0;
        let skippedCount = 0;

        for (let i = 0; i < emails.length; i++) {
            const email = emails[i];

            try {
                const text = `${email.subject || ''}\n\n${email.body || ''}`.trim();

                if (text.length < 5) {
                    console.log(`[${i + 1}/${emails.length}] Skipping: Text too short`);
                    skippedCount++;
                    continue;
                }

                const subjectPreview = (email.subject || '(no subject)').substring(0, 50);
                console.log(`[${i + 1}/${emails.length}] Classifying: ${subjectPreview}...`);

                // Call the classification API
                const classifyResponse = await axios.post('http://localhost:3000/api/emails/classify', {
                    text: text
                });

                const result = classifyResponse.data;

                if (result.category && result.category !== 'Unclassified' && result.serviceAvailable) {
                    console.log(`  ✓ ${result.category} (${(result.confidence * 100).toFixed(1)}%)`);

                    // Save the classification back to Elasticsearch
                    try {
                        await axios.patch(`http://localhost:3000/api/emails/${email.id}/classify`, {
                            category: result.category,
                            confidence: result.confidence
                        });
                        console.log(`  → Saved to database\n`);
                        successCount++;
                    } catch (saveError) {
                        console.error(`  ✗ Failed to save: ${saveError.message}\n`);
                        failCount++;
                    }
                } else {
                    console.log(`  ✗ ${result.error || 'Service unavailable'}\n`);
                    failCount++;
                }

                // Small delay to avoid overwhelming the service
                await new Promise(resolve => setTimeout(resolve, 200));

            } catch (error) {
                console.error(`  ✗ Error: ${error.message}\n`);
                failCount++;
            }
        }

        console.log('\n========================================');
        console.log('   Reclassification Complete!');
        console.log('========================================');
        console.log(`Total emails: ${emails.length}`);
        console.log(`Successfully classified & saved: ${successCount}`);
        console.log(`Failed: ${failCount}`);
        console.log(`Skipped (too short): ${skippedCount}`);
        console.log('========================================\n');

    } catch (error) {
        console.error('Fatal Error:', error.message);
        if (error.response) {
            console.error('Response:', error.response.data);
        }
    }
}

reclassifyAllEmails();

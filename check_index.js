const axios = require('axios');

async function checkIndices() {
    try {
        // Try to list all indices
        const esUrl = 'https://009e4f399df8495e8d901e235391571e.us-central1.gcp.cloud.es.io:443';
        const apiKey = process.env.ELASTICSEARCH_API_KEY;

        if (!apiKey) {
            console.log('❌ ELASTICSEARCH_API_KEY not set in environment');
            console.log('💡 Run this script with: ELASTICSEARCH_API_KEY=your_key node check_index.js');
            return;
        }

        console.log('Checking Elasticsearch indices...\n');

        // Check common index names
        const possibleIndices = ['emails', 'onebox_elastic', 'mails'];

        for (const indexName of possibleIndices) {
            try {
                const response = await axios.get(`${esUrl}/${indexName}/_count`, {
                    headers: {
                        'Authorization': `ApiKey ${apiKey}`
                    },
                    httpsAgent: new (require('https')).Agent({ rejectUnauthorized: false })
                });

                console.log(`✅ Index "${indexName}" exists`);
                console.log(`   Documents: ${response.data.count}`);
            } catch (error) {
                if (error.response?.status === 404) {
                    console.log(`❌ Index "${indexName}" does NOT exist`);
                } else {
                    console.log(`⚠️  Index "${indexName}" - Error: ${error.message}`);
                }
            }
        }

        console.log('\n📋 Recommendation:');
        console.log('Use the index name that has documents, or use "emails" as default');

    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkIndices();

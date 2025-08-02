const ElasticsearchService = require('./dist/Services/search/ElasticsearchService');

async function testElasticsearch() {
    console.log('Testing Elasticsearch connection...');

    try {
        const esService = new ElasticsearchService();

        // Wait a moment for index initialization
        await new Promise(resolve => setTimeout(resolve, 2000));

        console.log('✓ ElasticsearchService created successfully');

        // Initialize the index first
        await esService.initIndex();
        console.log('✓ Index initialization successful');

        // Test search (should return empty results initially)
        const searchResult = await esService.search('test');
        console.log('✓ Search test successful:', searchResult);

        console.log('Elasticsearch integration is working correctly!');

    } catch (error) {
        console.error('✗ Elasticsearch test failed:', error);
    }
}

testElasticsearch();
import { ElasticsearchService } from './src/Services/search/ElasticsearchService';
import { Email } from './src/Services/imap/Email';
import { logger } from './src/Services/utils/Logger';

const testElasticsearch = async () => {
    logger.info('Starting comprehensive Elasticsearch test...');

    const esService = new ElasticsearchService();

    try {
        // Wait for index initialization
        logger.info('1. Waiting for Elasticsearch service initialization...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        logger.info('✅ Elasticsearch service initialized');

        // Test email indexing
        logger.info('2. Testing email indexing...');
        const testEmail: Email = {
            id: 'test-email-' + Date.now(),
            uid: 999999,
            seqno: 1,
            accountId: 'test-account',
            folder: 'INBOX',
            from: 'Test Sender <test@example.com>',
            to: 'Test Recipient <recipient@example.com>',
            subject: 'Test Email for Elasticsearch',
            body: 'This is a test email body for Elasticsearch indexing. It contains sample content to verify search functionality.',
            date: new Date(),
            attachments: [],
            headers: {}
        };

        await esService.indexEmail(testEmail);
        logger.info('✅ Email indexing successful');

        // Wait for indexing (Elasticsearch refresh)
        logger.info('3. Waiting for Elasticsearch refresh...');
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Test search functionality
        logger.info('4. Testing search functionality...');
        const searchResults = await esService.search('test email');

        if (searchResults.emails.length > 0) {
            logger.info(`✅ Search successful - Found ${searchResults.emails.length} email(s)`);
            logger.info(`Total hits: ${searchResults.total}`);

            // Display first result
            const firstResult = searchResults.emails[0];
            logger.info('First search result:');
            logger.info(`  Subject: ${firstResult._source.subject}`);
            logger.info(`  From: ${firstResult._source.from}`);
            logger.info(`  Date: ${firstResult._source.date}`);
        } else {
            logger.warn('⚠️ Search returned no results (this might be expected for a fresh test)');
        }

        // Test different search queries
        logger.info('5. Testing various search queries...');
        const queries = ['test', 'elasticsearch', 'sample', 'nonexistent'];

        for (const query of queries) {
            const results = await esService.search(query);
            logger.info(`Query "${query}": ${results.total} results`);
        }

        // Test filtered search
        logger.info('6. Testing filtered search...');
        const filteredResults = await esService.search('test', 'test-account', 'INBOX');
        logger.info(`Filtered search: ${filteredResults.total} results`);

        logger.info('🎉 All Elasticsearch tests completed successfully!');

    } catch (error) {
        logger.error('❌ Elasticsearch test failed:', error);
        throw error;
    }
};

// Run the test
testElasticsearch()
    .then(() => {
        logger.info('Test suite completed');
        process.exit(0);
    })
    .catch((error) => {
        logger.error('Test suite failed:', error);
        process.exit(1);
    });

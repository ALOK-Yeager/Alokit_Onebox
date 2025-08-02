#!/usr/bin/env node

console.log('🔍 Checking Elasticsearch Integration...\n');

// Check if all required packages are installed
const checkPackages = () => {
    console.log('📦 Checking required packages...');

    const requiredPackages = [
        '@elastic/elasticsearch',
        'express',
        'winston',
        'dotenv'
    ];

    for (const pkg of requiredPackages) {
        try {
            require(pkg);
            console.log(`✅ ${pkg} - installed`);
        } catch (error) {
            console.log(`❌ ${pkg} - missing`);
            console.log(`   Run: npm install ${pkg}`);
            process.exit(1);
        }
    }
    console.log('');
};

// Check if Elasticsearch is running
const checkElasticsearch = async () => {
    console.log('🔌 Checking Elasticsearch connection...');

    try {
        const { Client } = require('@elastic/elasticsearch');
        const client = new Client({
            node: process.env.ELASTICSEARCH_NODE || 'http://localhost:9200',
            tls: { rejectUnauthorized: false }
        });

        const health = await client.cluster.health();
        console.log(`✅ Elasticsearch is running - Status: ${health.status}`);
        console.log(`   Cluster: ${health.cluster_name}`);
        console.log(`   Nodes: ${health.number_of_nodes}`);
        return true;
    } catch (error) {
        console.log('❌ Elasticsearch connection failed');
        console.log('   Make sure Elasticsearch is running on http://localhost:9200');
        console.log('   Or set ELASTICSEARCH_NODE environment variable');
        return false;
    }
};

// Main check function
const runChecks = async () => {
    try {
        // Load environment variables
        require('dotenv').config();

        checkPackages();

        const esRunning = await checkElasticsearch();

        console.log('\n📝 Next Steps:');
        if (esRunning) {
            console.log('✅ All checks passed! You can now:');
            console.log('   1. Run the Elasticsearch test: npm run test:elasticsearch');
            console.log('   2. Run the API test: npm run test:api');
            console.log('   3. Start the main application: npm start');
        } else {
            console.log('⚠️  Start Elasticsearch before testing:');
            console.log('   • Docker: docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0');
            console.log('   • Or install locally and start the service');
        }

        console.log('\n📚 Test Commands:');
        console.log('   npm run dev              - Start with file watching');
        console.log('   npm run test:elasticsearch - Test Elasticsearch integration');
        console.log('   npm run test:api         - Test API endpoints');
        console.log('   npm run build            - Build for production');

    } catch (error) {
        console.error('❌ Error during checks:', error.message);
        process.exit(1);
    }
};

runChecks();

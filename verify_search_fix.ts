import axios from 'axios';

const BASE_URL = 'http://localhost:3000/api/emails';

async function verifyEndpoints() {
    console.log('🚀 Starting API Verification...');

    // 1. Test Search (Single Category)
    try {
        console.log('\n1️⃣  Testing Search (Single Category)...');
        const res1 = await axios.get(`${BASE_URL}/search`, {
            params: { q: 'test', category: 'Interested' }
        });
        console.log('   ✅ Status:', res1.status);
        console.log('   📦 Results:', res1.data.count || 0);
    } catch (error) {
        console.log('   ❌ Failed:', error.message);
    }

    // 2. Test Search (Multiple Categories)
    try {
        console.log('\n2️⃣  Testing Search (Multiple Categories)...');
        const res2 = await axios.get(`${BASE_URL}/search`, {
            params: { q: 'test', categories: 'Interested,Important' }
        });
        console.log('   ✅ Status:', res2.status);
        console.log('   📦 Results:', res2.data.count || 0);
    } catch (error) {
        console.log('   ❌ Failed:', error.message);
    }

    // 3. Test Classification
    try {
        console.log('\n3️⃣  Testing Classification...');
        const res3 = await axios.post(`${BASE_URL}/classify`, {
            text: "Meeting next Tuesday at 10am to discuss the project."
        });
        console.log('   ✅ Status:', res3.status);
        console.log('   🏷️  Category:', res3.data.category);
    } catch (error) {
        console.log('   ❌ Failed:', error.message);
    }

    // 4. Test Get Email by ID (using a dummy ID, expect 404 or 200 if exists)
    try {
        console.log('\n4️⃣  Testing Get Email by ID...');
        const res4 = await axios.get(`${BASE_URL}/dummy-id-123`);
        console.log('   ✅ Status:', res4.status);
    } catch (error) {
        if (error.response && error.response.status === 404) {
            console.log('   ✅ Status: 404 (Expected for dummy ID)');
        } else {
            console.log('   ❌ Failed:', error.message);
        }
    }

    console.log('\n🏁 Verification Complete.');
}

verifyEndpoints();

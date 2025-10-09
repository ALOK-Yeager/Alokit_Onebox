import { useState } from 'react';
import EmailSearchUI from './components/EmailSearchUI';
import './App.css';

function App() {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-indigo-600">Alokit_Onebox</h1>
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setShowDemo(!showDemo)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
              >
                {showDemo ? 'Hide Live Demo' : 'Try it Live!'}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="bg-white">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
            <span className="block">Revolutionize Your Inbox</span>
            <span className="block text-indigo-600">Alokit_Onebox</span>
          </h1>
          <p className="mt-6 max-w-lg mx-auto text-xl text-gray-500 sm:max-w-3xl">
            The AI-Powered Email Mastery Tool. Seamlessly pulling together all your inboxes into one intuitive platform.
          </p>
        </div>
      </header>

      {/* Interactive Demo Section */}
      {showDemo && (
        <main className="py-16">
          <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div className="bg-white shadow-xl rounded-lg overflow-hidden">
              <EmailSearchUI />
            </div>
          </div>
        </main>
      )}
    </div>
  );
}

export default App;
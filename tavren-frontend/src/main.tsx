import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Assuming App component will be in ./App.tsx
import { AuthProvider } from './AuthContext'; // Updated to correct path
import './style.css'

const rootElement = document.getElementById('root'); // Ensure you have <div id="root"></div> in your index.html

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <AuthProvider>
        <App />
      </AuthProvider>
    </React.StrictMode>
  );
} else {
  console.error("Failed to find the root element. Ensure an element with id 'root' exists in your index.html.");
}

// Remove the old vanilla TS code below if it exists
// document.querySelector<HTMLDivElement>('#app')!.innerHTML = ...
// setupCounter(...)

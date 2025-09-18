import React from 'react';
import { createRoot } from 'react-dom/client'; // 👈 new import for React 18
import App from './App';

const container = document.getElementById('root');
const root = createRoot(container); // 👈 create a root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
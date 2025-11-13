import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import PopulationPage from './pages/PopulationPage';
import ParetoPage from './pages/ParetoPage';
import ExplainPage from './pages/ExplainPage';
import AdvisorPage from './pages/AdvisorPage';
import './App.css';

function App() {
  return (
    <div className="App min-h-screen bg-background text-foreground">
      <BrowserRouter>
        <div className="flex">
          <Sidebar />
          <main className="flex-1 ml-64">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/population" element={<PopulationPage />} />
              <Route path="/pareto" element={<ParetoPage />} />
              <Route path="/explain" element={<ExplainPage />} />
              <Route path="/advisor" element={<AdvisorPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
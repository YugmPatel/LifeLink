import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ErrorBoundary from "./components/common/ErrorBoundary";

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gray-950 text-white">
          <Layout />
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;

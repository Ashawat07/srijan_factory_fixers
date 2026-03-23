import React, { useState } from 'react';
import './App.css';
import Home from './pages/Home';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import TechnicianPortal from './pages/TechnicianPortal';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [currentUser, setCurrentUser] = useState(null);

  const navigate = (page, user = null) => {
    setCurrentPage(page);
    if (user) setCurrentUser(user);
  };

  return (
    <div>
      {currentPage === 'home'       && <Home             navigate={navigate} />}
      {currentPage === 'login'      && <Login            navigate={navigate} />}
      {currentPage === 'admin'      && <AdminDashboard   navigate={navigate} user={currentUser} />}
      {currentPage === 'technician' && <TechnicianPortal navigate={navigate} user={currentUser} />}
    </div>
  );
}

export default App;
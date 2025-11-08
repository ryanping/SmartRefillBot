import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom';
import LoginPage from './LoginPage';
import './App.css'

function Dashboard() {
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    fetch('/api/requests')
      .then(res => res.json())
      .then(data => setRequests(data));
  }, []);

  const handleApprove = (id) => {
    fetch(`/api/approve/${id}`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        console.log(data.message);
        // Remove the approved request from the list
        setRequests(requests.filter(req => req.id !== id));
      });
  };

  return (
    <div className="dashboard-container">
      <h1>Refill Requests</h1>
      <table>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Medication</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {requests.map(req => (
            <tr key={req.id}>
              <td>{req.patient}</td>
              <td>{req.medication}</td>
              <td><button onClick={() => handleApprove(req.id)}>Approve</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}

export default App

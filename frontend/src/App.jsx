import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom';
import LoginPage from './LoginPage';
import './Dashboard.css';
import './App.css'

function Dashboard() {
  const [requests, setRequests] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);

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

  const patients = [...new Set(requests.map(req => req.patient))];
  const selectedRequest = requests.find(req => req.patient === selectedPatient);

  return (
    <div className="dashboard-container">
      <div className="sidebar">
        <h2>Messages</h2>
        <ul>
          {patients.map(patient => (
            <li key={patient} onClick={() => setSelectedPatient(patient)} className={selectedPatient === patient ? 'active' : ''}>
              {patient}
            </li>
          ))}
        </ul>
      </div>
      <div className="messaging-panel">
        {selectedPatient && selectedRequest ? (
          <>
            <div className="messaging-header">
              <h3>{selectedPatient}</h3>
              <p>Requesting: {selectedRequest.medication}</p>
            </div>
            <div className="message-body">
              {/* Future messaging UI goes here */}
              <p>Messaging interface for {selectedPatient}.</p>
            </div>
            <div className="message-footer">
              <button onClick={() => handleApprove(selectedRequest.id)}>Approve Request</button>
            </div>
          </>
        ) : (
          <div className="placeholder">Select a patient to start messaging.</div>
        )}
      </div>
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

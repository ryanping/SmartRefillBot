import React, { useState } from 'react';
import './AdminPage.css';

function AdminPage() {
  const [email, setEmail] = useState('');
  const [showPopup, setShowPopup] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (email) {
      setShowPopup(true);
    }
  };

  const handleConfirm = () => {
    console.log(`Creating account for: ${email}`);
    // In a real app, you would make an API call here to create the account.
    setShowPopup(false);
    setEmail(''); // Optionally clear the email input
  };

  const handleCancel = () => {
    setShowPopup(false);
  };

  return (
    <div className="admin-container">
    <h1>Smart Refiller</h1>
      <h1>Admin Page: Creating New Accounts</h1>
      <form onSubmit={handleSubmit} className="admin-form">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter user's email"
          required
        />
        <button type="submit">Create Account</button>
      </form>

      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <h2>Confirm Account Creation</h2>
            <p>Are you sure you want to create an account for <strong>{email}</strong>?</p>
            <div className="popup-buttons">
              <button onClick={handleConfirm} className="yes-button">Yes</button>
              <button onClick={handleCancel} className="no-button">No</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPage;
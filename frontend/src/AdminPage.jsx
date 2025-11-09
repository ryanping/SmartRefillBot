import React, { useState } from 'react';
import './AdminPage.css';

function AdminPage() {
  const [email, setEmail] = useState('');
  const [showPopup, setShowPopup] = useState(false);
  const [action, setAction] = useState('post'); // 'post' or 'delete'

  const handleSubmit = (event) => {
    event.preventDefault();
    if (email) {
      setShowPopup(true);
    }
  };

  const handleConfirm = () => {
    if (action === 'post') {
      console.log(`Creating account for: ${email}`);
      // In a real app, you would make an API call here to create the account.
    } else {
      console.log(`Deleting account for: ${email}`);
      // In a real app, you would make an API call here to delete the account.
    }
    setShowPopup(false);
    setEmail(''); // Optionally clear the email input
  };

  const handleCancel = () => {
    setShowPopup(false);
  };

  const pageTitle = action === 'post' ? 'Admin Page: Creating New Accounts' : 'Admin Page: Deleting Accounts';
  const buttonText = action === 'post' ? 'Create Account' : 'Delete Account';
  const popupTitle = action === 'post' ? 'Confirm Account Creation' : 'Confirm Account Deletion';
  const popupMessage = action === 'post'
    ? `Are you sure you want to create an account for <strong>${email}</strong>?`
    : `Are you sure you want to delete the account for <strong>${email}</strong>?`;

  return (
    <div className="admin-container">
      <h1>Smart Refiller</h1>
      <h1>{pageTitle}</h1>

      <div className="admin-form">
        <label htmlFor="action-select">Action:</label>
        <select id="action-select" value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="post">Create User</option>
          <option value="delete">Delete User</option>
        </select>
      </div>

      <form onSubmit={handleSubmit} className="admin-form">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter user's email"
          required
        />
        <button type="submit">{buttonText}</button>
      </form>

      {showPopup && (
        <div className="popup-overlay">
          <div className="popup">
            <h2>{popupTitle}</h2>
            <p dangerouslySetInnerHTML={{ __html: popupMessage }} />
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
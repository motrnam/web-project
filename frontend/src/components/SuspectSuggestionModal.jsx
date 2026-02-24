import React from "react";

const SuspectSuggestionModal = ({ boardId, onClose, onSuccess }) => {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0,0,0,0.5)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          backgroundColor: "white",
          padding: "20px",
          borderRadius: "8px",
          maxWidth: "500px",
          width: "90%",
        }}
      >
        <h2>Suggest Suspects</h2>
        <p>This feature is coming soon...</p>
        <button
          onClick={onClose}
          style={{
            padding: "8px 16px",
            backgroundColor: "#3498db",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            marginTop: "10px",
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default SuspectSuggestionModal;

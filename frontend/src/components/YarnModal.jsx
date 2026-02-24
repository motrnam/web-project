import { useState } from "react";

const YarnModal = ({ boardId, leads, onClose, onSave }) => {
  const [lead1, setLead1] = useState("");
  const [lead2, setLead2] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave({
        lead1: parseInt(lead1),
        lead2: parseInt(lead2),
      });
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    overlay: {
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(0, 0, 0, 0.7)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 1000,
    },
    modal: {
      backgroundColor: "#1a1e24",
      border: "2px solid #2c3e50",
      borderRadius: "8px",
      padding: "20px",
      width: "400px",
      maxWidth: "90%",
      color: "#ecf0f1",
    },
    header: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "20px",
      paddingBottom: "10px",
      borderBottom: "2px solid #2c3e50",
    },
    title: {
      fontSize: "20px",
      color: "#e0b84d",
      margin: 0,
      fontFamily: "Courier New, monospace",
    },
    closeButton: {
      background: "none",
      border: "none",
      color: "#95a5a6",
      fontSize: "24px",
      cursor: "pointer",
    },
    formGroup: {
      marginBottom: "15px",
    },
    label: {
      display: "block",
      marginBottom: "5px",
      color: "#95a5a6",
      fontSize: "14px",
    },
    select: {
      width: "100%",
      padding: "8px",
      backgroundColor: "#2c3e50",
      border: "1px solid #3d5a73",
      borderRadius: "4px",
      color: "#ecf0f1",
      fontSize: "14px",
    },
    buttonGroup: {
      display: "flex",
      justifyContent: "flex-end",
      gap: "10px",
      marginTop: "20px",
    },
    button: {
      padding: "8px 16px",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "14px",
      transition: "background-color 0.3s",
    },
    saveButton: {
      backgroundColor: "#3d5a73",
      color: "white",
    },
    cancelButton: {
      backgroundColor: "#2c3e50",
      color: "#95a5a6",
    },
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h2 style={styles.title}>Connect Leads</h2>
          <button style={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label style={styles.label}>First Lead</label>
            <select
              style={styles.select}
              value={lead1}
              onChange={(e) => setLead1(e.target.value)}
              required
            >
              <option value="">Select Lead</option>
              {leads.map((lead) => (
                <option key={lead.id} value={lead.id}>
                  {lead.title} ({lead.lead_type === "E" ? "Evidence" : "Note"})
                </option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Second Lead</label>
            <select
              style={styles.select}
              value={lead2}
              onChange={(e) => setLead2(e.target.value)}
              required
            >
              <option value="">Select Lead</option>
              {leads.map((lead) => (
                <option key={lead.id} value={lead.id}>
                  {lead.title} ({lead.lead_type === "E" ? "Evidence" : "Note"})
                </option>
              ))}
            </select>
          </div>

          <div style={styles.buttonGroup}>
            <button
              type="button"
              style={{ ...styles.button, ...styles.cancelButton }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ ...styles.button, ...styles.saveButton }}
              disabled={loading || !lead1 || !lead2 || lead1 === lead2}
            >
              {loading ? "Connecting..." : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default YarnModal;

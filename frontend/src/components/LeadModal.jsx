import { useState, useEffect } from "react";

const LeadModal = ({ lead, onClose, onSave, onDelete }) => {
  const [formData, setFormData] = useState({
    title: "",
    lead_type: "N",
    content: "",
    evidence: null,
    position_x: 0.5,
    position_y: 0.5,
  });
  const [evidences, setEvidences] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (lead) {
      setFormData({
        title: lead.title || "",
        lead_type: lead.lead_type || "N",
        content: lead.content || "",
        evidence: lead.evidence || null,
        position_x: lead.position_x || 0.5,
        position_y: lead.position_y || 0.5,
      });
    }

    // Fetch available evidences
    fetchEvidences();
  }, [lead]);

  const fetchEvidences = async () => {
    try {
      const response = await fetch("/api/evidences/evidences/", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setEvidences(data);
      }
    } catch (error) {
      console.error("Failed to fetch evidences:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave(formData);
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
      width: "500px",
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
    input: {
      width: "100%",
      padding: "8px",
      backgroundColor: "#2c3e50",
      border: "1px solid #3d5a73",
      borderRadius: "4px",
      color: "#ecf0f1",
      fontSize: "14px",
    },
    textarea: {
      width: "100%",
      padding: "8px",
      backgroundColor: "#2c3e50",
      border: "1px solid #3d5a73",
      borderRadius: "4px",
      color: "#ecf0f1",
      fontSize: "14px",
      minHeight: "100px",
      resize: "vertical",
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
    deleteButton: {
      backgroundColor: "#922a2a",
      color: "white",
      marginRight: "auto",
    },
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h2 style={styles.title}>{lead ? "Edit Lead" : "New Lead"}</h2>
          <button style={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Title</label>
            <input
              type="text"
              style={styles.input}
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Type</label>
            <select
              style={styles.select}
              value={formData.lead_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  lead_type: e.target.value,
                  evidence: null,
                  content: "",
                })
              }
            >
              <option value="N">Detective Note</option>
              <option value="E">Evidence</option>
            </select>
          </div>

          {formData.lead_type === "N" ? (
            <div style={styles.formGroup}>
              <label style={styles.label}>Content</label>
              <textarea
                style={styles.textarea}
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                required
              />
            </div>
          ) : (
            <div style={styles.formGroup}>
              <label style={styles.label}>Evidence</label>
              <select
                style={styles.select}
                value={formData.evidence || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    evidence: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
                required
              >
                <option value="">Select Evidence</option>
                {evidences.map((evidence) => (
                  <option key={evidence.id} value={evidence.id}>
                    {evidence.title || `Evidence #${evidence.id}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={styles.formGroup}>
            <label style={styles.label}>Position X (0-1)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="0.99"
              style={styles.input}
              value={formData.position_x}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  position_x: parseFloat(e.target.value),
                })
              }
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Position Y (0-1)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="0.99"
              style={styles.input}
              value={formData.position_y}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  position_y: parseFloat(e.target.value),
                })
              }
              required
            />
          </div>

          <div style={styles.buttonGroup}>
            {onDelete && (
              <button
                type="button"
                style={{ ...styles.button, ...styles.deleteButton }}
                onClick={onDelete}
              >
                Delete
              </button>
            )}
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
              disabled={loading}
            >
              {loading ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LeadModal;

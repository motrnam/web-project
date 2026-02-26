import { useState, useEffect, useCallback } from "react";
import LeadModal from "./LeadModal";
import YarnModal from "./YarnModal";
import SuspectSuggestionModal from "./SuspectSuggestionModal";

const handleLeadClick = (lead) => {
  if (connectingMode) {
    if (selectedLeadForConnection) {
      if (selectedLeadForConnection.id !== lead.id) {
        // Create yarn between the two leads
        handleCreateYarn({
          lead1: selectedLeadForConnection.id,
          lead2: lead.id,
        });
      }
      setConnectingMode(false);
      setSelectedLeadForConnection(null);
    } else {
      setSelectedLeadForConnection(lead);
    }
  }
};

const handleCreateLead = async (leadData) => {
  try {
    const response = await fetch("/api/detection/leads/", {
      method: "POST",
      headers: {
        Authorization: `Token ${localStorage.getItem("access_token")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...leadData,
        board_id: boardId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to create lead");
    }

    await fetchBoardData();
    setShowLeadModal(false);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const handleUpdateLead = async (leadData) => {
  if (!selectedLead) return;

  try {
    const response = await fetch(`/api/detection/leads/${selectedLead.id}/`, {
      method: "PUT",
      headers: {
        Authorization: `Token ${localStorage.getItem("access_token")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...leadData,
        board_id: boardId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to update lead");
    }

    await fetchBoardData();
    setShowLeadModal(false);
    setSelectedLead(null);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const handleDeleteLead = async (leadId) => {
  try {
    const response = await fetch(`/api/detection/leads/${leadId}/`, {
      method: "DELETE",
      headers: {
        Authorization: `Token ${localStorage.getItem("access_token")}`,
      },
    });

    if (!response.ok) throw new Error("Failed to delete lead");

    await fetchBoardData();
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const handleCreateYarn = async (yarnData) => {
  try {
    const response = await fetch("/api/detection/yarns/", {
      method: "POST",
      headers: {
        Authorization: `Token ${localStorage.getItem("access_token")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(yarnData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to create connection");
    }

    await fetchBoardData();
    setShowYarnModal(false);
    setConnectingMode(false);
    setSelectedLeadForConnection(null);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const handleDeleteYarn = async (yarnId) => {
  try {
    const response = await fetch(`/api/detection/yarns/${yarnId}/`, {
      method: "DELETE",
      headers: {
        Authorization: `Token ${localStorage.getItem("access_token")}`,
      },
    });

    if (!response.ok) throw new Error("Failed to delete connection");

    await fetchBoardData();
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};

const DetectiveBoard = ({ boardId, boardData, onBoardUpdate, permissions }) => {
  const [leads, setLeads] = useState([]);
  const [yarns, setYarns] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [showYarnModal, setShowYarnModal] = useState(false);
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [connectingMode, setConnectingMode] = useState(false);
  const [selectedLeadForConnection, setSelectedLeadForConnection] =
    useState(null);

  const canEdit = permissions.includes("cases.edit");
  const canCreateLeads = permissions.includes("leads.create");
  const canSuggestSuspects = permissions.includes("suspects.suggest");

  // Fetch board data
  const fetchBoardData = useCallback(async () => {
    if (!boardId) return;

    setLoading(true);
    try {
      const [leadsRes, yarnsRes, suggestionsRes] = await Promise.all([
        fetch(`/api/detection/boards/${boardId}/leads/`, {
          headers: {
            Authorization: `Token ${localStorage.getItem("access_token")}`,
          },
        }),
        fetch(`/api/detection/boards/${boardId}/yarns/`, {
          headers: {
            Authorization: `Token ${localStorage.getItem("access_token")}`,
          },
        }),
        fetch(`/api/detection/boards/${boardId}/suggestions/`, {
          headers: {
            Authorization: `Token ${localStorage.getItem("access_token")}`,
          },
        }),
      ]);

      if (!leadsRes.ok) throw new Error("Failed to fetch leads");

      const leadsData = await leadsRes.json();
      setLeads(leadsData);

      if (yarnsRes.ok) {
        const yarnsData = await yarnsRes.json();
        setYarns(yarnsData);
      }

      if (suggestionsRes.ok) {
        const suggestionsData = await suggestionsRes.json();
        setSuggestions(suggestionsData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  useEffect(() => {
    fetchBoardData();
  }, [fetchBoardData]);

  // Rest of your DetectiveBoard logic here...
  // (Keep all the existing handlers and render logic)

  return (
    <div style={styles.container}>
      {/* Toolbar with permission-based buttons */}
      <div style={styles.toolbar}>
        {canCreateLeads && (
          <button
            style={styles.toolButton}
            onClick={() => {
              setSelectedLead(null);
              setShowLeadModal(true);
            }}
          >
            + New Lead
          </button>
        )}

        {canCreateLeads && leads.length >= 2 && (
          <button
            style={{
              ...styles.toolButton,
              ...(connectingMode ? styles.toolButtonActive : {}),
            }}
            onClick={() => setConnectingMode(!connectingMode)}
          >
            {connectingMode ? "Cancel" : "Connect Leads"}
          </button>
        )}

        {canSuggestSuspects && (
          <button
            style={styles.toolButton}
            onClick={() => setShowSuggestionModal(true)}
          >
            Suggest Suspects
          </button>
        )}
      </div>

      {/* Leads display */}
      <div style={styles.leadsContainer}>
        {leads.map((lead) => (
          <div
            key={lead.id}
            style={{
              ...styles.lead,
              ...(lead.lead_type === "E"
                ? styles.leadEvidence
                : styles.leadNote),
              left: `${lead.position_x * 80 + 10}%`,
              top: `${lead.position_y * 70 + 15}%`,
              cursor: canEdit ? "pointer" : "default",
            }}
            onClick={() => canEdit && handleLeadClick(lead)}
            onContextMenu={(e) => {
              if (canEdit) {
                e.preventDefault();
                setSelectedLead(lead);
                setShowLeadModal(true);
              }
            }}
          >
            <div style={styles.leadTitle}>{lead.title}</div>
            {lead.lead_type === "N" && (
              <div style={styles.leadContent}>{lead.content}</div>
            )}
            {lead.lead_type === "E" && lead.evidence_details && (
              <div style={styles.leadContent}>
                <div>Type: {lead.evidence_details.evidence_type}</div>
                {lead.evidence_details.description && (
                  <div>
                    {lead.evidence_details.description.substring(0, 50)}...
                  </div>
                )}
              </div>
            )}
            <div style={styles.leadType}>
              {lead.lead_type === "E" ? "EVIDENCE" : "NOTE"}
            </div>
          </div>
        ))}

        {/* Yarns rendering */}
        <svg style={styles.yarnCanvas}>
          {yarns.map((yarn) => {
            const lead1 = leads.find((l) => l.id === yarn.lead1);
            const lead2 = leads.find((l) => l.id === yarn.lead2);

            if (!lead1 || !lead2) return null;

            const x1 = parseFloat(lead1.position_x) * 80 + 10 + 10;
            const y1 = parseFloat(lead1.position_y) * 70 + 15 + 10;
            const x2 = parseFloat(lead2.position_x) * 80 + 10 + 10;
            const y2 = parseFloat(lead2.position_y) * 70 + 15 + 10;

            return (
              <g key={yarn.id}>
                <line
                  x1={`${x1}%`}
                  y1={`${y1}%`}
                  x2={`${x2}%`}
                  y2={`${y2}%`}
                  style={styles.yarnLine}
                />
                {canEdit && (
                  <circle
                    cx={`${(x1 + x2) / 2}%`}
                    cy={`${(y1 + y2) / 2}%`}
                    r="6"
                    fill="#e0b84d"
                    style={styles.yarnDot}
                    onClick={() => {
                      if (window.confirm("Remove this connection?")) {
                        handleDeleteYarn(yarn.id);
                      }
                    }}
                  />
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Modals */}
      {showLeadModal && (
        <LeadModal
          lead={selectedLead}
          onClose={() => {
            setShowLeadModal(false);
            setSelectedLead(null);
          }}
          onSave={selectedLead ? handleUpdateLead : handleCreateLead}
          onDelete={
            selectedLead ? () => handleDeleteLead(selectedLead.id) : null
          }
        />
      )}

      {showYarnModal && (
        <YarnModal
          boardId={boardId}
          leads={leads}
          onClose={() => {
            setShowYarnModal(false);
            setConnectingMode(false);
            setSelectedLeadForConnection(null);
          }}
          onSave={handleCreateYarn}
        />
      )}

      {showSuggestionModal && (
        <SuspectSuggestionModal
          boardId={boardId}
          onClose={() => setShowSuggestionModal(false)}
          onSuccess={() => {
            fetchBoardData();
            setShowSuggestionModal(false);
          }}
        />
      )}
    </div>
  );
};

export default DetectiveBoard;

import React from "react";

const BoardList = ({ boards, onBoardSelect, canCreate, onCreateNew }) => {
  // Calculate case statistics
  const stats = {
    total: boards.length,
    active: boards.filter((b) => b.status === "active").length,
    pending: boards.filter((b) => b.status === "pending_review").length,
    closed: boards.filter((b) => b.status === "closed").length,
  };

  return (
    <div style={styles.container}>
      {/* Header with stats */}
      <div style={styles.header}>
        <h2 style={styles.title}>Active Cases</h2>
        <div style={styles.stats}>
          <div style={styles.stat}>
            <span style={styles.statValue}>{stats.total}</span>
            <span style={styles.statLabel}>Total</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statValue}>{stats.active}</span>
            <span style={styles.statLabel}>Active</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statValue}>{stats.pending}</span>
            <span style={styles.statLabel}>Pending</span>
          </div>
        </div>
        {canCreate && (
          <button onClick={onCreateNew} style={styles.newButton}>
            + New Case
          </button>
        )}
      </div>

      {/* Board List */}
      {boards.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No cases assigned</p>
          {canCreate && (
            <button onClick={onCreateNew} style={styles.emptyStateButton}>
              Create your first case
            </button>
          )}
        </div>
      ) : (
        <div style={styles.boardGrid}>
          {boards.map((board) => (
            <div
              key={board.id}
              style={styles.boardCard}
              onClick={() => onBoardSelect(board)}
            >
              <div style={styles.cardHeader}>
                <span style={styles.caseId}>
                  Case #{board.case_id?.slice(0, 8)}
                </span>
                <span
                  style={{
                    ...styles.status,
                    ...styles[`status${board.status || "active"}`],
                  }}
                >
                  {board.status || "Active"}
                </span>
              </div>
              <h3 style={styles.caseTitle}>
                {board.case_title || "Untitled Case"}
              </h3>
              <div style={styles.cardMeta}>
                <div style={styles.metaItem}>
                  <span style={styles.metaLabel}>Leads:</span>
                  <span style={styles.metaValue}>{board.leads_count || 0}</span>
                </div>
                <div style={styles.metaItem}>
                  <span style={styles.metaLabel}>Sergeant:</span>
                  <span style={styles.metaValue}>
                    {board.sergeant_name || "Unassigned"}
                  </span>
                </div>
              </div>
              <div style={styles.progressBar}>
                <div
                  style={{
                    ...styles.progress,
                    width: `${board.progress || 0}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: "20px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "30px",
  },
  title: {
    fontSize: "24px",
    color: "#2c3e50",
    margin: 0,
  },
  stats: {
    display: "flex",
    gap: "20px",
  },
  stat: {
    textAlign: "center",
  },
  statValue: {
    display: "block",
    fontSize: "24px",
    fontWeight: "bold",
    color: "#3498db",
  },
  statLabel: {
    fontSize: "12px",
    color: "#7f8c8d",
    textTransform: "uppercase",
  },
  newButton: {
    padding: "10px 20px",
    backgroundColor: "#3498db",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
  },
  boardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: "20px",
  },
  boardCard: {
    backgroundColor: "white",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    cursor: "pointer",
    transition: "transform 0.2s, box-shadow 0.2s",
    border: "1px solid #ecf0f1",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
  },
  caseId: {
    fontSize: "12px",
    color: "#7f8c8d",
    fontFamily: "monospace",
  },
  status: {
    padding: "2px 8px",
    borderRadius: "12px",
    fontSize: "11px",
    fontWeight: "bold",
    textTransform: "uppercase",
  },
  statusactive: {
    backgroundColor: "#d4edda",
    color: "#155724",
  },
  statuspending_review: {
    backgroundColor: "#fff3cd",
    color: "#856404",
  },
  statusclosed: {
    backgroundColor: "#f8d7da",
    color: "#721c24",
  },
  caseTitle: {
    fontSize: "16px",
    color: "#2c3e50",
    margin: "0 0 15px 0",
  },
  cardMeta: {
    marginBottom: "15px",
  },
  metaItem: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "5px",
    fontSize: "13px",
  },
  metaLabel: {
    color: "#7f8c8d",
  },
  metaValue: {
    color: "#2c3e50",
    fontWeight: "500",
  },
  progressBar: {
    height: "4px",
    backgroundColor: "#ecf0f1",
    borderRadius: "2px",
    overflow: "hidden",
  },
  progress: {
    height: "100%",
    backgroundColor: "#3498db",
    borderRadius: "2px",
  },
  emptyState: {
    textAlign: "center",
    padding: "60px 20px",
    backgroundColor: "white",
    borderRadius: "8px",
    border: "2px dashed #ecf0f1",
  },
  emptyStateButton: {
    padding: "10px 20px",
    backgroundColor: "#3498db",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    marginTop: "20px",
  },
};

export default BoardList;

import { useState, useEffect, useCallback } from "react";
import BoardList from "../components/BoardList";
import DetectiveBoard from "../components/DetectiveBoard";

const CasesModule = ({ user, permissions }) => {
  const [boards, setBoards] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState("list"); // 'list' or 'board'

  // Fetch all boards
  const fetchBoards = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "/api/detection/boards/?assigned_to_me=true",
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to fetch boards");

      const data = await response.json();
      setBoards(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBoards();
  }, [fetchBoards]);

  const handleBoardSelect = (board) => {
    setSelectedBoard(board);
    setView("board");
  };

  const handleBackToList = () => {
    setSelectedBoard(null);
    setView("list");
  };

  if (loading) {
    return <div style={styles.loading}>Loading cases...</div>;
  }

  if (error) {
    return <div style={styles.error}>Error: {error}</div>;
  }

  return (
    <div style={styles.container}>
      {view === "list" ? (
        <BoardList
          boards={boards}
          onBoardSelect={handleBoardSelect}
          canCreate={permissions.includes("cases.create")}
          onCreateNew={() => {
            /* Handle create new case */
          }}
        />
      ) : (
        <div style={styles.boardContainer}>
          <div style={styles.boardHeader}>
            <button onClick={handleBackToList} style={styles.backButton}>
              ← Back to Cases
            </button>
            <h2 style={styles.boardTitle}>
              Case: {selectedBoard?.case_title || "Untitled"}
            </h2>
          </div>
          <DetectiveBoard
            boardId={selectedBoard?.id}
            boardData={selectedBoard}
            onBoardUpdate={fetchBoards}
            permissions={permissions}
          />
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    height: "100%",
  },
  boardContainer: {
    height: "100%",
  },
  boardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "20px",
    marginBottom: "20px",
    padding: "10px",
    backgroundColor: "#f8f9fa",
    borderRadius: "4px",
  },
  backButton: {
    padding: "8px 16px",
    backgroundColor: "white",
    border: "1px solid #bdc3c7",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    color: "#34495e",
  },
  boardTitle: {
    fontSize: "18px",
    color: "#2c3e50",
    margin: 0,
  },
  loading: {
    textAlign: "center",
    padding: "40px",
    color: "#7f8c8d",
  },
  error: {
    textAlign: "center",
    padding: "40px",
    color: "#e74c3c",
  },
};

export default CasesModule;

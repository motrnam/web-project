import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import ModulesRegistry from "./ModulesRegistry";

const Dashboard = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [userPermissions, setUserPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user permissions from backend
  useEffect(() => {
    console.log("Dashboard rendering", {
      isAuthenticated,
      user,
      loading,
      error,
      permissions: userPermissions,
    });

    if (!isAuthenticated) return;

    const fetchPermissions = async () => {
      try {
        const response = await fetch("/api/users/roles/", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });

        if (!response.ok) throw new Error("Failed to fetch permissions");

        const data = await response.json();
        setUserPermissions(data.permissions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPermissions();
  }, [isAuthenticated]);

  // Redirect if not authenticated
  if (!isAuthenticated) {
    navigate("/login");
    return null;
  }

  // Loading state
  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loadingSpinner} />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={styles.errorContainer}>
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <button
          onClick={() => window.location.reload()}
          style={styles.retryButton}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header - Common for all modules */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.headerTitle}>LAPD Detective Bureau</h1>
          <span style={styles.badge}>Badge #{user?.national_id || "N/A"}</span>
        </div>
        <div style={styles.userInfo}>
          <span style={styles.userName}>
            Det. {user?.full_name || user?.username}
          </span>
          <button onClick={logout} style={styles.logoutButton}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Modules Registry - Renders modules based on permissions */}
      <ModulesRegistry user={user} permissions={userPermissions} />
    </div>
  );
};

// Styles - Kept separate for cleaner code
const styles = {
  container: {
    maxWidth: "1600px",
    margin: "0 auto",
    padding: "20px",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px",
    backgroundColor: "white",
    borderRadius: "8px",
    marginBottom: "20px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "20px",
  },
  headerTitle: {
    fontSize: "24px",
    color: "#2c3e50",
    margin: 0,
  },
  badge: {
    padding: "4px 12px",
    backgroundColor: "#ecf0f1",
    borderRadius: "20px",
    fontSize: "14px",
    color: "#7f8c8d",
  },
  userInfo: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
  },
  userName: {
    fontSize: "14px",
    color: "#34495e",
  },
  logoutButton: {
    padding: "8px 16px",
    backgroundColor: "#e74c3c",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background-color 0.2s",
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
  },
  loadingSpinner: {
    width: "40px",
    height: "40px",
    border: "3px solid #f3f3f3",
    borderTop: "3px solid #3498db",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
    marginBottom: "20px",
  },
  errorContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
    padding: "20px",
  },
  retryButton: {
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

export default Dashboard;

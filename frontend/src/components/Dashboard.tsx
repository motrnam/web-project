//frontend/src/components/Dashboard.tsx
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import ModulesRegistry from "./ModulesRegistry";

const Dashboard = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  console.log("Dashboard - User:", user);
  console.log("Dashboard - User groups:", user?.groups);

  if (!isAuthenticated) {
    navigate("/login");
    return null;
  }

  // Determine permissions based on user's groups
  const userPermissions = [];

  // Check if user is a Detective (case-sensitive match your group name)
  if (user?.groups?.includes("Detective")) {
    userPermissions.push(
      "cases.view",
      "cases.create",
      "leads.create",
      "suspects.suggest",
      "cases.edit",
    );
  } else {
    // Basic permission for all authenticated users
    userPermissions.push("cases.view");
  }

  console.log("Dashboard - Permissions:", userPermissions);

  const styles = {
    container: {
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "20px",
    },
    header: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      padding: "15px 20px",
      backgroundColor: "#f8f9fa",
      borderRadius: "8px",
      marginBottom: "30px",
    },
    headerTitle: {
      fontSize: "24px",
      color: "#333",
      margin: 0,
    },
    logoutButton: {
      padding: "8px 16px",
      backgroundColor: "#dc3545",
      color: "white",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "14px",
    },
    content: {
      backgroundColor: "white",
      borderRadius: "8px",
      padding: "20px",
      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      minHeight: "500px",
    },
  };

  return (
    <div style={styles.container}>
      {/* Header with Logout */}
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>
          L.A. Noire Dashboard - Detective {user?.full_name || user?.username}
        </h1>
        <button onClick={logout} style={styles.logoutButton}>
          Logout
        </button>
      </header>

      {/* Main Content */}
      <div style={styles.content}>
        <ModulesRegistry user={user} permissions={userPermissions} />
      </div>
    </div>
  );
};

export default Dashboard;

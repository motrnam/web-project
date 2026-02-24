import { useState } from "react";
import CasesModule from "../modules/CasesModule";
import EvidenceModule from "../modules/EvidenceModule";
import InterrogationModule from "../modules/InterrogationModule";
import ReportsModule from "../modules/ReportsModule";

// Module configurations based on permissions
const MODULE_CONFIG = {
  "cases.view": {
    component: CasesModule,
    title: "Active Cases",
    icon: "📋",
    priority: 1,
    gridSize: "large", // large, medium, small
  },
  "evidence.view": {
    component: EvidenceModule,
    title: "Evidence Locker",
    icon: "🔍",
    priority: 2,
    gridSize: "medium",
  },
  "interrogation.view": {
    component: InterrogationModule,
    title: "Interrogations",
    icon: "💬",
    priority: 3,
    gridSize: "medium",
  },
  "reports.view": {
    component: ReportsModule,
    title: "Reports",
    icon: "📊",
    priority: 4,
    gridSize: "small",
  },
};

const ModulesRegistry = ({ user, permissions }) => {
  const [activeModule, setActiveModule] = useState(null);
  const [moduleProps, setModuleProps] = useState({});

  // Filter modules based on user permissions - MOVED THIS AFTER useState
  const availableModules = Object.entries(MODULE_CONFIG)
    .filter(([permission]) => permissions.includes(permission))
    .map(([_, config]) => config)
    .sort((a, b) => a.priority - b.priority);

  console.log("ModulesRegistry rendering", {
    user,
    permissions,
    availableModules: availableModules.length,
  });

  // Handle module navigation
  const handleModuleSelect = (module, props = {}) => {
    setActiveModule(module);
    setModuleProps(props);
  };

  // Handle back to dashboard
  const handleBackToDashboard = () => {
    setActiveModule(null);
    setModuleProps({});
  };

  // If a specific module is active, render it fullscreen
  if (activeModule) {
    const ModuleComponent = activeModule.component;
    return (
      <div style={styles.fullscreenModule}>
        <div style={styles.moduleHeader}>
          <button onClick={handleBackToDashboard} style={styles.backButton}>
            ← Back to Dashboard
          </button>
          <h2 style={styles.moduleTitle}>
            {activeModule.icon} {activeModule.title}
          </h2>
        </div>
        <div style={styles.moduleContent}>
          <ModuleComponent
            user={user}
            permissions={permissions}
            {...moduleProps}
          />
        </div>
      </div>
    );
  }

  // Otherwise render the dashboard grid
  return (
    <div style={styles.dashboard}>
      {/* Welcome Section */}
      <div style={styles.welcomeSection}>
        <h2 style={styles.welcomeTitle}>
          Welcome back, Detective{" "}
          {user?.full_name?.split(" ")[0] || user?.username}
        </h2>
        <p style={styles.welcomeText}>
          You have {availableModules.length} modules available
        </p>
      </div>

      {/* Modules Grid */}
      <div style={styles.modulesGrid}>
        {availableModules.map((module, index) => (
          <div
            key={index}
            style={{
              ...styles.moduleCard,
              ...styles[`${module.gridSize}Card`],
            }}
            onClick={() => handleModuleSelect(module)}
          >
            <div style={styles.moduleIcon}>{module.icon}</div>
            <h3 style={styles.moduleCardTitle}>{module.title}</h3>
            <p style={styles.moduleCardDescription}>
              Click to open {module.title.toLowerCase()}
            </p>
          </div>
        ))}
      </div>

      {/* Quick Actions - Based on permissions */}
      <div style={styles.quickActions}>
        <h3 style={styles.quickActionsTitle}>Quick Actions</h3>
        <div style={styles.quickActionsGrid}>
          {permissions.includes("cases.create") && (
            <button style={styles.quickAction}>➕ New Case</button>
          )}
          {permissions.includes("evidence.create") && (
            <button style={styles.quickAction}>🔍 Log Evidence</button>
          )}
          {permissions.includes("reports.create") && (
            <button style={styles.quickAction}>📄 Generate Report</button>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  dashboard: {
    padding: "20px 0",
  },
  welcomeSection: {
    marginBottom: "30px",
  },
  welcomeTitle: {
    fontSize: "28px",
    color: "#2c3e50",
    margin: "0 0 10px 0",
  },
  welcomeText: {
    fontSize: "16px",
    color: "#7f8c8d",
    margin: 0,
  },
  modulesGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: "20px",
    marginBottom: "40px",
  },
  moduleCard: {
    backgroundColor: "white",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    cursor: "pointer",
    transition: "transform 0.2s, box-shadow 0.2s",
    border: "1px solid #ecf0f1",
    "&:hover": {
      transform: "translateY(-5px)",
      boxShadow: "0 4px 8px rgba(0,0,0,0.15)",
    },
  },
  largeCard: {
    gridColumn: "span 2",
  },
  mediumCard: {
    gridColumn: "span 1",
  },
  smallCard: {
    gridColumn: "span 1",
  },
  moduleIcon: {
    fontSize: "32px",
    marginBottom: "15px",
  },
  moduleCardTitle: {
    fontSize: "18px",
    color: "#2c3e50",
    margin: "0 0 10px 0",
  },
  moduleCardDescription: {
    fontSize: "14px",
    color: "#7f8c8d",
    margin: 0,
    lineHeight: "1.5",
  },
  quickActions: {
    backgroundColor: "white",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  quickActionsTitle: {
    fontSize: "18px",
    color: "#2c3e50",
    margin: "0 0 15px 0",
  },
  quickActionsGrid: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  },
  quickAction: {
    padding: "10px 20px",
    backgroundColor: "#ecf0f1",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    color: "#34495e",
    transition: "background-color 0.2s",
    "&:hover": {
      backgroundColor: "#d5dbdb",
    },
  },
  fullscreenModule: {
    backgroundColor: "white",
    borderRadius: "8px",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    overflow: "hidden",
  },
  moduleHeader: {
    display: "flex",
    alignItems: "center",
    gap: "20px",
    padding: "20px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #ecf0f1",
  },
  backButton: {
    padding: "8px 16px",
    backgroundColor: "transparent",
    border: "1px solid #bdc3c7",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    color: "#7f8c8d",
    transition: "all 0.2s",
    "&:hover": {
      backgroundColor: "#ecf0f1",
      borderColor: "#95a5a6",
    },
  },
  moduleTitle: {
    fontSize: "20px",
    color: "#2c3e50",
    margin: 0,
  },
  moduleContent: {
    padding: "20px",
    minHeight: "600px",
  },
};

export default ModulesRegistry;

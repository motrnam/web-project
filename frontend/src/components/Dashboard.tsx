//frontend/src/components/Dashboard.tsx
import {useAuth} from '../context/AuthContext';
import {useNavigate} from 'react-router-dom';

const Dashboard = () => {
    const {user, logout, isAuthenticated} = useAuth();
    const navigate = useNavigate();

    if (!isAuthenticated) {
        navigate('/login');
        return null;
    }

    const styles = {
        container: {
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '20px',
        },
        header: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '15px 20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            marginBottom: '30px',
        },
        headerTitle: {
            fontSize: '24px',
            color: '#333',
            margin: 0,
        },
        logoutButton: {
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
        },
        dashboardGrid: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
        },
        module: {
            backgroundColor: 'white',
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
        moduleTitle: {
            fontSize: '18px',
            color: '#333',
            marginTop: 0,
            marginBottom: '15px',
            paddingBottom: '10px',
            borderBottom: '2px solid #007bff',
        },
        profileInfo: {
            lineHeight: '1.8',
        },
        profileLabel: {
            fontWeight: 'bold',
            color: '#555',
            marginRight: '10px',
        },
        profileValue: {
            color: '#333',
        },
        placeholderModule: {
            backgroundColor: '#f8f9fa',
            textAlign: 'center' as const,
            color: '#666',
            padding: '40px 20px',
        },
    };

    return (
        <div style={styles.container}>
            {/* Header with Logout */}
            <header style={styles.header}>
                <h1 style={styles.headerTitle}>L.A. Noire Dashboard</h1>
                <button onClick={logout} style={styles.logoutButton}>
                    Logout
                </button>
            </header>

            {/* Dashboard Modules Grid */}
            <div style={styles.dashboardGrid}>
                {/* Profile Module */}
                <div style={styles.module}>
                    <h3 style={styles.moduleTitle}>👤 Profile Information</h3>
                    <div style={styles.profileInfo}>
                        <p>
                            <span style={styles.profileLabel}>Username:</span>
                            <span style={styles.profileValue}>{user?.username}</span>
                        </p>
                        <p>
                            <span style={styles.profileLabel}>Full Name:</span>
                            <span style={styles.profileValue}>{user?.full_name}</span>
                        </p>
                        <p>
                            <span style={styles.profileLabel}>National ID:</span>
                            <span style={styles.profileValue}>{user?.national_id}</span>
                        </p>
                        <p>
                            <span style={styles.profileLabel}>Phone:</span>
                            <span style={styles.profileValue}>{user?.phone_number}</span>
                        </p>
                        <p>
                            <span style={styles.profileLabel}>Email:</span>
                            <span style={styles.profileValue}>{user?.email}</span>
                        </p>
                    </div>
                </div>

                {/* Placeholder Module 1 */}
                <div style={{...styles.module, ...styles.placeholderModule}}>
                    <h3 style={styles.moduleTitle}>📊 Statistics</h3>
                    <p>Module under development</p>
                </div>

                {/* Placeholder Module 2 */}
                <div style={{...styles.module, ...styles.placeholderModule}}>
                    <h3 style={styles.moduleTitle}>📝 Recent Activity</h3>
                    <p>Module under development</p>
                </div>

                {/* Placeholder Module 3 */}
                <div style={{...styles.module, ...styles.placeholderModule}}>
                    <h3 style={styles.moduleTitle}>⚙️ Settings</h3>
                    <p>Module under development</p>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
//frontend/src/components/Login.tsx
import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';

const API_BASE_URL = 'http://localhost:8000/api';

const Login = () => {
    const navigate = useNavigate();
    const {login} = useAuth();

    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Use the login endpoint (now returns complete user data)
            const res = await fetch(`${API_BASE_URL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await res.json();

            if (res.ok) {
                // data.user now contains ALL user fields (thanks to your backend change)
                login(data.token, data.user);
                navigate('/dashboard');
            } else {
                setError(data.error || 'Invalid username or password');
            }
        } catch (err) {
            setError('Network error. Please check your connection.');
        } finally {
            setLoading(false);
        }
    };

    const styles = {
        container: {
            maxWidth: '350px',
            margin: '40px auto',
            padding: '20px',
        },
        form: {
            padding: '20px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            backgroundColor: '#fff',
        },
        title: {
            textAlign: 'center' as const,
            color: '#333',
            marginBottom: '20px',
        },
        formGroup: {
            marginBottom: '15px',
            textAlign: 'left' as const,
        },
        label: {
            display: 'block',
            marginBottom: '5px',
            color: '#555',
            fontWeight: '500',
        },
        input: {
            width: '100%',
            padding: '10px',
            borderRadius: '4px',
            border: '1px solid #ddd',
            fontSize: '14px',
        },
        button: {
            width: '100%',
            padding: '12px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '500',
            marginTop: '10px',
        },
        buttonDisabled: {
            backgroundColor: '#ccc',
            cursor: 'not-allowed',
        },
        error: {
            marginTop: '15px',
            padding: '10px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: '4px',
            textAlign: 'center' as const,
        },
        link: {
            textAlign: 'center' as const,
            marginTop: '15px',
            color: '#666',
        },
    };

    return (
        <div style={styles.container}>
            <form onSubmit={handleSubmit} style={styles.form}>
                <h2 style={styles.title}>Login to L.A. Noire</h2>

                <div style={styles.formGroup}>
                    <label style={styles.label}>ورود با نام کاربری / کد ملی / شماره / ایمیل:</label>
                    <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        style={styles.input}
                        placeholder="نام کاربری، کد ملی، شماره تلفن یا ایمیل"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label style={styles.label}>Password:</label>
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                        style={styles.input}
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    style={{...styles.button, ...(loading ? styles.buttonDisabled : {})}}
                >
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                {error && (
                    <div style={styles.error}>
                        {error}
                    </div>
                )}

                <div style={styles.link}>
                    Don't have an account? <Link to="/register">Register here</Link>
                </div>
            </form>
        </div>
    );
};

export default Login;
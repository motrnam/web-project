import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';

const API_BASE_URL = 'http://localhost:8000/api';

const Register = () => {
    const navigate = useNavigate();
    const {login} = useAuth();

    const [formData, setFormData] = useState({
        username: '',
        password: '',
        full_name: '',
        national_id: '',
        phone_number: '',
        email: ''
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
            console.log('Registration data:', formData);

            const res = await fetch(`${API_BASE_URL}/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            console.log('Response status:', res.status);

            const data = await res.json();
            console.log('Response data:', data);

            if (res.ok) {
                login(data.token, data.user);
                navigate('/dashboard');
            } else {
                // Show the actual error message from the server
                if (data.username) {
                    setError(`Username: ${data.username.join(', ')}`);
                } else if (data.email) {
                    setError(`Email: ${data.email.join(', ')}`);
                } else if (data.national_id) {
                    setError(`National ID: ${data.national_id.join(', ')}`);
                } else if (data.phone_number) {
                    setError(`Phone number: ${data.phone_number.join(', ')}`);
                } else if (data.password) {
                    setError(`Password: ${data.password.join(', ')}`);
                } else if (data.message) {
                    setError(data.message);
                } else if (typeof data === 'object') {
                    // Generic error display for any other field errors
                    const errors = Object.entries(data)
                        .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                        .join('\n');
                    setError(errors || 'Registration failed. Please check your information.');
                } else {
                    setError('Registration failed. Please try again.');
                }
            }
        } catch (err) {
            console.error('Fetch error:', err);
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const styles = {
        container: {
            maxWidth: '400px',
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
            backgroundColor: '#007bff',
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
                <h2 style={styles.title}>Create Account</h2>

                <div style={styles.formGroup}>
                    <label style={styles.label}>Username:</label>
                    <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        style={styles.input}
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

                <div style={styles.formGroup}>
                    <label style={styles.label}>Full Name:</label>
                    <input
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleChange}
                        required
                        style={styles.input}
                    />
                </div>

                <div style={styles.formGroup}>
                    <label style={styles.label}>National ID:</label>
                    <input
                        type="text"
                        name="national_id"
                        value={formData.national_id}
                        onChange={handleChange}
                        required
                        style={styles.input}
                    />
                </div>

                <div style={styles.formGroup}>
                    <label style={styles.label}>Phone Number:</label>
                    <input
                        type="text"
                        name="phone_number"
                        value={formData.phone_number}
                        onChange={handleChange}
                        required
                        style={styles.input}
                    />
                </div>

                <div style={styles.formGroup}>
                    <label style={styles.label}>Email:</label>
                    <input
                        type="email"
                        name="email"
                        value={formData.email}
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
                    {loading ? 'Creating Account...' : 'Register'}
                </button>

                {error && (
                    <div style={styles.error}>
                        {error}
                    </div>
                )}

                <div style={styles.link}>
                    Already have an account? <Link to="/login">Login here</Link>
                </div>
            </form>
        </div>
    );
};

export default Register;
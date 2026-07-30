import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Lock, Mail, LogIn, Loader2 } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);
      const response = await axios.post(
        `${API_BASE}/api/auth/login`,
        params,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );
      localStorage.setItem("admin_token", response.data.access_token);
      navigate("/admin");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string" ? detail : "Invalid credentials or server error"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <Lock size={32} />
        </div>
        <h1 className="login-title">Dr. Khare AI</h1>
        <p className="login-subtitle">Admin Control Panel</p>

        {error && (
          <div className="login-error" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="login-form">
          <div className="login-field">
            <label htmlFor="email" className="login-label">
              Email Address
            </label>
            <div className="login-input-wrap">
              <Mail size={16} className="login-input-icon" />
              <input
                id="email"
                type="email"
                className="login-input"
                placeholder="admin@khare.ai"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="login-field">
            <label htmlFor="password" className="login-label">
              Password
            </label>
            <div className="login-input-wrap">
              <Lock size={16} className="login-input-icon" />
              <input
                id="password"
                type="password"
                className="login-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>
          </div>

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading || !email.trim() || !password.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="login-spin" />
                Authenticating...
              </>
            ) : (
              <>
                <LogIn size={18} />
                Secure Login
              </>
            )}
          </button>
        </form>

        <p className="login-footer">
          Protected by JWT • Dr. Supreet Khare AI System
        </p>
      </div>

      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 50%, #f8fafc 100%);
          padding: 1.5rem;
          font-family: 'Inter', -apple-system, sans-serif;
        }

        .login-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(12px);
          border: 1px solid #e2e8f0;
          border-radius: 20px;
          padding: 2.5rem 2rem;
          width: 100%;
          max-width: 400px;
          box-shadow: 0 20px 60px rgba(15, 23, 42, 0.1);
          text-align: center;
          animation: loginFadeIn 0.4s ease;
        }

        @keyframes loginFadeIn {
          from { opacity: 0; transform: translateY(-16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .login-logo {
          width: 64px;
          height: 64px;
          margin: 0 auto 1.25rem;
          border-radius: 16px;
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3);
        }

        .login-title {
          margin: 0 0 0.35rem;
          font-size: 1.6rem;
          font-weight: 700;
          color: #0f172a;
          letter-spacing: -0.02em;
        }

        .login-subtitle {
          margin: 0 0 1.75rem;
          color: #64748b;
          font-size: 0.9rem;
        }

        .login-error {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
          border-radius: 10px;
          padding: 0.75rem 1rem;
          font-size: 0.88rem;
          margin-bottom: 1.25rem;
          text-align: left;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          text-align: left;
        }

        .login-field {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .login-label {
          font-size: 0.82rem;
          font-weight: 600;
          color: #475569;
        }

        .login-input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }

        .login-input-icon {
          position: absolute;
          left: 12px;
          color: #94a3b8;
          pointer-events: none;
        }

        .login-input {
          width: 100%;
          padding: 0.75rem 0.875rem 0.75rem 2.5rem;
          border: 1px solid #cbd5e1;
          border-radius: 10px;
          font-size: 0.95rem;
          color: #0f172a;
          background: #f8fafc;
          transition: border-color 0.2s, box-shadow 0.2s;
          box-sizing: border-box;
        }

        .login-input:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
          background: white;
        }

        .login-input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .login-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          width: 100%;
          padding: 0.875rem;
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          color: white;
          border: none;
          border-radius: 10px;
          font-size: 0.95rem;
          font-weight: 600;
          cursor: pointer;
          margin-top: 0.5rem;
          transition: transform 0.2s, box-shadow 0.2s;
          box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }

        .login-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
        }

        .login-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .login-spin {
          animation: loginSpin 0.8s linear infinite;
        }

        @keyframes loginSpin {
          to { transform: rotate(360deg); }
        }

        .login-footer {
          margin: 1.5rem 0 0;
          font-size: 0.72rem;
          color: #94a3b8;
        }
      `}</style>
    </div>
  );
}

export default Login;

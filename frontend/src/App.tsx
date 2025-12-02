import { createContext, useContext, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import "./App.css";
import LoginPage from "./pages/LoginPage";
import HomeDashboard from "./pages/HomeDashboard";
import AthenaIaChatPage from "./pages/AthenaIaChatPage";
import AdminDashboard from "./pages/AdminDashboard";
import ProfilePage from "./pages/ProfilePage";
import { getMe } from "./services/api";
import type { User } from "./types";

type AuthContextType = {
  user: User | null;
  token: string | null;
  setAuth: (tok: string, usr: User) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);
const useAuth = () => useContext(AuthContext);

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const auth = useAuth();
  if (!auth?.token || !auth.user) return <Navigate to="/login" replace />;
  return children;
}

function AdminRoute({ children }: { children: JSX.Element }) {
  const auth = useAuth();
  const isAdmin = auth?.user?.role === "admin" || auth?.user?.is_admin;
  if (!auth?.token || !auth.user) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/home" replace />;
  return children;
}

function HomeWrapper() {
  const auth = useAuth();
  const navigate = useNavigate();
  if (!auth?.user || !auth.token) return <Navigate to="/login" replace />;
  return (
    <HomeDashboard
      user={auth.user}
      token={auth.token}
      onLogout={() => {
        auth.logout();
        navigate("/login");
      }}
      onOpenChat={(path) => navigate(path ?? "/chat")}
    />
  );
}

function ChatWrapper() {
  const auth = useAuth();
  const navigate = useNavigate();
  const { chatId } = useParams();
  if (!auth?.user || !auth.token) return <Navigate to="/login" replace />;
  return (
    <AthenaIaChatPage
      user={auth.user}
      token={auth.token}
      chatIdParam={chatId}
      onBack={() => navigate("/home")}
      onLogout={() => {
        auth.logout();
        navigate("/login");
      }}
    />
  );
}

function AdminWrapper() {
  const auth = useAuth();
  const navigate = useNavigate();
  if (!auth?.user || !auth.token) return <Navigate to="/login" replace />;
  return (
    <AdminDashboard
      user={auth.user}
      token={auth.token}
      onBack={() => navigate("/home")}
      onLogout={() => {
        auth.logout();
        navigate("/login");
      }}
    />
  );
}

function ProfileWrapper() {
  const auth = useAuth();
  const navigate = useNavigate();
  if (!auth?.user || !auth.token) return <Navigate to="/login" replace />;
  return (
    <ProfilePage
      user={auth.user}
      token={auth.token}
      onBack={() => navigate("/home")}
      onLogout={() => {
        auth.logout();
        navigate("/login");
      }}
    />
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("athena_token");
    if (!saved) {
      setChecking(false);
      return;
    }
    (async () => {
      try {
        const me = await getMe(saved);
        const role = me.role || (me.is_admin ? "admin" : "usuario");
        setUser({ ...me, role });
        setToken(saved);
      } catch {
        localStorage.removeItem("athena_token");
      } finally {
        setChecking(false);
      }
    })();
  }, []);

  const setAuth = (tok: string, usr: User) => {
    localStorage.setItem("athena_token", tok);
    const role = usr.role || (usr.is_admin ? "admin" : "usuario");
    setUser({ ...usr, role });
    setToken(tok);
  };

  const logout = () => {
    localStorage.removeItem("athena_token");
    setToken(null);
    setUser(null);
  };

  if (checking) {
    return (
      <div className="shell">
        <main className="shell-main">
          <p className="muted">Carregando...</p>
        </main>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, token, setAuth, logout }}>
      <BrowserRouter>
        <Routes>

          {/* LOGIN */}
          <Route
            path="/login"
            element={
              <LoginPage
                onLoginSuccess={(tok, usr) => {
                  setAuth(tok, usr);
                }}
              />
            }
          />

          {/* PÁGINAS */}
          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <HomeWrapper />
              </ProtectedRoute>
            }
          />

          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatWrapper />
              </ProtectedRoute>
            }
          />

          <Route
            path="/chat/:chatId"
            element={
              <ProtectedRoute>
                <ChatWrapper />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfileWrapper />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          <Route
            path="/admin/users"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          <Route
            path="/admin/policies"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          <Route
            path="/admin/config"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          <Route
            path="/admin/audit"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          <Route
            path="/admin/feedback"
            element={
              <AdminRoute>
                <AdminWrapper />
              </AdminRoute>
            }
          />

          {/* DEFAULT */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to={token ? "/home" : "/login"} replace />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

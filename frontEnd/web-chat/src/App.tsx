import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import ChatPage from './pages/chatPage';
import RegisterPage from './pages/registerPage';
import LoginPage from './pages/loginPage';

function App() {
    return (
        <Router>
            <Routes> <Route path="/" element={<Navigate to="/login" replace />} />


                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/chat/:conversationId" element={<ChatPage />} />

                <Route path="*" element={<Navigate to="/login" replace />} /></Routes>

        </Router>
    )
}

export default App;


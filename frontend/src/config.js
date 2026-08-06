// Centralized API configuration
// Uses VITE_API_URL env var, falling back to the local backend.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper to get the stored JWT
export const getToken = () => localStorage.getItem('token');

export const getUsername = () => localStorage.getItem('username');

export const setAuth = (token, username) => {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
};

export const clearAuth = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
};

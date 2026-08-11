// Centralized API configuration
// Uses `VITE_API_URL` when provided. During development the dev server
// proxy forwards `/api` to the backend so we prefer an empty default
// which results in relative `/api` requests (avoiding CORS issues).
export const API_URL = import.meta.env.VITE_API_URL ?? '';

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

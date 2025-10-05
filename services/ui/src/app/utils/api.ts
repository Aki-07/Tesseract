import axios from "axios";
console.log("NEXT_PUBLIC_API_URL at runtime:", process.env.NEXT_PUBLIC_API_URL);

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL
});

export default api;

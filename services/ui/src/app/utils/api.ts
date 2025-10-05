import axios from "axios";
console.log("NEXT_PUBLIC_API_URL at runtime:", process.env.NEXT_PUBLIC_API_URL);

const api = axios.create({
  baseURL:
    process.env.NEXT_PUBLIC_API_URL || "https://tesseract-ptnh.onrender.com",
});

export default api;

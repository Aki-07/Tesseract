import axios from "axios";
console.log("NEXT_PUBLIC_API_URL at runtime:", process.env.NEXT_PUBLIC_API_URL);

const api =
  process.env.NEXT_PUBLIC_API_URL || "https://tesseract-ptnh.onrender.com";

console.log("NEXT_PUBLIC_API_URL at runtime:", api);
export default api;

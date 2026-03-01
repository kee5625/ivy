import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import JobDetailsPage from "./pages/graph/graph";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/graph/:jobId" element={<JobDetailsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

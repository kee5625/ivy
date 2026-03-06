import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import JobDetailsPage from "./pages/graph/graph";
import Hero from "./pages/hero";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/graph/:jobId" element={<JobDetailsPage />} />
        <Route path="/test" element={<Hero />} />
      </Routes>
    </BrowserRouter>
  );
}

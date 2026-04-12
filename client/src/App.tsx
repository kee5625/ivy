import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import JobDetailsPage from "./pages/graph/graph";
import Hero from "./pages/hero";
import ResultsPage from "./pages/results";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/graph/:jobId" element={<JobDetailsPage />} />
        <Route path="/results/:jobId" element={<ResultsPage />} />
        <Route path="/test" element={<Hero />} />
      </Routes>
    </BrowserRouter>
  );
}

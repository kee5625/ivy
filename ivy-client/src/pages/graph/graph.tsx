import { useParams } from "react-router-dom";

export default function JobDetailsPage() {
  const { jobId } = useParams();

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f4fbf1] via-[#fbfef9] to-[#f5faf3] px-5 py-10 text-[#2f503d] sm:px-8 lg:px-12">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-[#234231] sm:text-5xl">
            Graph Visualization
          </h1>
          <p className="mt-2 text-lg text-[#4f6e5a]">
            Job ID: <span className="font-semibold">{jobId}</span>
          </p>
        </div>

        {/* Graph placeholder */}
        <div className="rounded-3xl border border-[#c5dfbf] bg-white/92 p-8 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.35)]">
          <div className="flex h-96 items-center justify-center rounded-lg border-2 border-dashed border-[#b8d5b1] bg-[#f6fbf3]">
            <p className="text-center text-[#5b7865]">
              Graph visualization for job {jobId} will be rendered here
            </p>
          </div>
        </div>

        {/* Job details placeholder */}
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-2xl border border-[#c5dfbf] bg-white/92 p-6">
            <h2 className="text-sm font-semibold tracking-wide text-[#5a7b64] uppercase">Status</h2>
            <p className="mt-2 text-2xl font-bold text-[#234231]">Processing</p>
          </div>
          <div className="rounded-2xl border border-[#c5dfbf] bg-white/92 p-6">
            <h2 className="text-sm font-semibold tracking-wide text-[#5a7b64] uppercase">Progress</h2>
            <p className="mt-2 text-2xl font-bold text-[#234231]">0%</p>
          </div>
          <div className="rounded-2xl border border-[#c5dfbf] bg-white/92 p-6">
            <h2 className="text-sm font-semibold tracking-wide text-[#5a7b64] uppercase">Files</h2>
            <p className="mt-2 text-2xl font-bold text-[#234231]">0</p>
          </div>
        </div>
      </div>
    </div>
  );
}

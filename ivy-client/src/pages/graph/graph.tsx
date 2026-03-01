import { useParams } from "react-router-dom";
import type { JobStatusProps } from '@/types/types';
import { JobStatus } from "@/components/job-status";
import { useState } from "react";

export default function JobDetailsPage() {
  const { jobId } = useParams();
  const [jobStatus, setJobStatus] = useState<JobStatusProps>({
    jobId: jobId || "unknown",
    status: "pending",
    progress: 0,
    message: "Job is pending..."
  })

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
            <JobStatus {...jobStatus} />
          </div>
        </div>
      </div>
    </div>
  );
}

import { useMemo, useState } from "react";
import axios from 'axios'

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileSize = useMemo(() => {
    if (!selectedFile) {
      return "";
    }

    const mb = selectedFile.size / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  }, [selectedFile]);
  
  const handleFileSubmit = async () => {
    if (!selectedFile) {
      alert("Please upload a PDF before submitting");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("original_filename", selectedFile.name);
    formData.append("file_size", String(selectedFile.size));
    formData.append("mime_type", selectedFile.type || "application/pdf");

    try {
      setIsUploading(true);
      const response = await axios.post("/api/pdf/parse", formData);
      const uploadedName = response.data?.data?.filename ?? selectedFile.name;
      const chunkCount = response.data?.data?.chunks?.length ?? 0;

      alert(`Uploaded ${uploadedName} successfully (${chunkCount} chunks).`);
    } catch (e) {
      alert("Failed to upload file.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-[#f4fbf1] via-[#fbfef9] to-[#f5faf3] px-5 py-10 text-[#2f503d] sm:px-8 lg:px-12">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-14 top-14 h-44 w-44 rounded-full bg-[#d8ebd2]/65 blur-2xl" />
        <div className="absolute -right-20 top-10 h-56 w-56 rounded-full bg-[#e5f3df]/80 blur-3xl" />
        <div className="absolute left-1/2 top-0 h-10 w-[120%] -translate-x-1/2 rounded-b-[999px] border-b border-[#b9d7b3]/70 bg-[#eff8eb]/70" />
        <div className="absolute left-[8%] top-6 h-12 w-40 rotate-3 rounded-full border border-[#aacda5]/60" />
        <div className="absolute right-[10%] top-7 h-12 w-52 -rotate-2 rounded-full border border-[#aacda5]/60" />
      </div>

      <main className="relative mx-auto flex w-full max-w-4xl flex-col gap-10 pt-8 sm:pt-12">
        <section className="space-y-5 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-[#234231] sm:text-5xl md:text-6xl">
            Ivy
          </h1>
          <p className="mx-auto max-w-2xl text-base leading-relaxed text-[#4f6e5a] sm:text-lg">
            Upload your pdf. Watch the magic happen.
          </p>
        </section>

        <section className="mx-auto w-full max-w-2xl rounded-3xl border border-[#c5dfbf] bg-white/92 p-6 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.35)] sm:p-8">
          <div className="mb-6 space-y-1.5">
            <h2 className="text-2xl font-bold text-[#2b4a37]">Select a PDF</h2>
            <p className="text-sm text-[#5b7865]">
              Drag and drop or browse your files. Only PDF format is accepted.
            </p>
          </div>

          <label
            htmlFor="pdf-upload"
            className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-[#b8d5b1] bg-[#f6fbf3] px-5 py-5 text-center transition hover:border-[#8dbf88] hover:bg-[#f2faed]"
          >
            <span className="text-lg font-semibold text-[#2f4f3b]">
              Click to choose a file
            </span>
            <span className="text-sm text-[#5d7a67]">
              Maximum one document per upload.
            </span>
            <input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              className="sr-only"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelectedFile(file);
              }}
            />
          </label>

          <div className="mt-5 flex items-center justify-between gap-3 rounded-xl border border-[#d4e8ce] bg-[#fcfefb] px-4 py-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold tracking-wide text-[#5a7b64] uppercase">
                Selected file
              </p>
              <p className="truncate text-sm text-[#355342]">
                {selectedFile ? selectedFile.name : "No file selected yet"}
              </p>
            </div>
            {selectedFile ? (
              <span className="shrink-0 rounded-full border border-[#c6e0c0] bg-[#eef8ea] px-3 py-1 text-xs font-semibold text-[#477054]">
                {fileSize}
              </span>
            ) : null}
          </div>

          <button
            type="button"
            onClick={handleFileSubmit}
            disabled={!selectedFile || isUploading}
            className="mt-6 w-full rounded-xl bg-[#4f8957] px-5 py-3 text-sm font-semibold tracking-wide text-white transition hover:bg-[#42774a] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#94c596] focus-visible:ring-offset-2"
          >
            {isUploading ? "Uploading..." : "Upload PDF"}
          </button>
        </section>
      </main>
    </div>
  );
}

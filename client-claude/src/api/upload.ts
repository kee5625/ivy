type PresignResponse = { presigned_url: string; object_key: string };
type DirectUploadResult = { objectKey: string };
type CreateJobResponse = { job_id: string };

function ensurePdf(file: File): void {
  const isPdfType = file.type === "application/pdf";
  const isPdfName = file.name.toLowerCase().endsWith(".pdf");
  if (!isPdfType && !isPdfName) throw new Error("Only PDF uploads are supported");
}

async function requestPresignedUrl(file: File): Promise<PresignResponse> {
  const res = await fetch("/api/upload/presign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, content_type: file.type || "application/pdf", size: file.size }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Presign failed: ${res.status} ${text}`);
  }
  return (await res.json()) as PresignResponse;
}

export async function uploadPdfDirectToR2(file: File): Promise<DirectUploadResult> {
  ensurePdf(file);
  const { presigned_url, object_key } = await requestPresignedUrl(file);
  const up = await fetch(presigned_url, {
    method: "PUT",
    headers: { "Content-Type": file.type || "application/pdf" },
    body: file,
  });
  if (!up.ok) throw new Error(`R2 upload failed: ${up.status}`);
  return { objectKey: object_key };
}

export async function createJob(filename: string, objectKey: string): Promise<string> {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, object_key: objectKey }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Job creation failed: ${res.status} ${text}`);
  }
  const data = (await res.json()) as CreateJobResponse;
  return data.job_id;
}

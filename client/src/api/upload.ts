type PresignResponse = {
  presigned_url: string;
  object_key: string;
};

type DirectUploadResult = {
  objectKey: string;
};

type CreateJobResponse = {
  job_id: string;
};

function logUpload(event: string, data?: Record<string, unknown>): void {
  if (data) {
    console.info(`[upload] ${event}`, data);
    return;
  }
  console.info(`[upload] ${event}`);
}

function ensurePdfFile(file: File): void {
  const isPdfType = file.type === "application/pdf";
  const isPdfName = file.name.toLowerCase().endsWith(".pdf");

  if (!isPdfType && !isPdfName) {
    throw new Error("Only PDF uploads are supported");
  }
}

async function requestPresignedUrl(file: File): Promise<PresignResponse> {
  const response = await fetch("/api/upload/presign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type || "application/pdf",
      size: file.size,
    }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Presign request failed: ${response.status} ${text}`);
  }

  return (await response.json()) as PresignResponse;
}

export async function uploadPdfDirectToR2(file: File): Promise<DirectUploadResult> {
  logUpload("start", { filename: file.name, size: file.size });

  ensurePdfFile(file);

  const { presigned_url, object_key } = await requestPresignedUrl(file);
  logUpload("presign_received", { object_key });

  const uploadResponse = await fetch(presigned_url, {
    method: "PUT",
    headers: { "Content-Type": file.type || "application/pdf" },
    body: file,
  });

  if (!uploadResponse.ok) {
    throw new Error(`R2 upload failed: ${uploadResponse.status}`);
  }

  logUpload("success", { object_key });
  return { objectKey: object_key };
}

export async function createJob(
  filename: string,
  objectKey: string,
): Promise<string> {
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, object_key: objectKey }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Job creation failed: ${response.status} ${text}`);
  }

  const data = (await response.json()) as CreateJobResponse;
  return data.job_id;
}

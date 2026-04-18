export type SignUploadRequest = {
  filename: string;
  contentType: string;
  size: number;
};

export type SignUploadResponse = {
  uploadUrl: string;
  objectKey: string;
  headers?: Record<string, string>;
};

function ensurePdfRequest(payload: SignUploadRequest): void {
  const isPdfType = payload.contentType === "application/pdf";
  const isPdfName = payload.filename.toLowerCase().endsWith(".pdf");

  if (!isPdfType && !isPdfName) {
    throw new Error("Only PDF uploads are supported");
  }
}

export async function requestUploadSignature(
  payload: SignUploadRequest,
): Promise<SignUploadResponse> {
  ensurePdfRequest(payload);

  const response = await fetch("/api/upload", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to sign upload (${response.status})`);
  }

  return (await response.json()) as SignUploadResponse;
}

export async function uploadFileToSignedUrl(
  uploadUrl: string,
  file: File,
  headers?: Record<string, string>,
): Promise<void> {
  const uploadResponse = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/pdf",
      ...headers,
    },
    body: file,
  });

  if (!uploadResponse.ok) {
    throw new Error(`Direct upload failed (${uploadResponse.status})`);
  }
}

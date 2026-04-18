import { PutObjectCommand, S3Client } from "@aws-sdk/client-s3";

type DirectUploadResult = {
  objectKey: string;
  objectUrl: string | null;
};

function logUpload(event: string, data?: Record<string, unknown>): void {
  if (data) {
    console.info(`[upload] ${event}`, data);
    return;
  }

  console.info(`[upload] ${event}`);
}

function assertEnv(name: string): string {
  const value = import.meta.env[name as keyof ImportMetaEnv];

  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`Missing required env var: ${name}`);
  }

  return value.trim();
}

function ensurePdfFile(file: File): void {
  const isPdfType = file.type === "application/pdf";
  const isPdfName = file.name.toLowerCase().endsWith(".pdf");

  if (!isPdfType && !isPdfName) {
    throw new Error("Only PDF uploads are supported");
  }
}

function sanitizeFilename(filename: string): string {
  return filename
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9._-]/g, "")
    .replace(/-+/g, "-");
}

function createObjectKey(filename: string): string {
  const now = new Date();
  const y = now.getUTCFullYear();
  const m = String(now.getUTCMonth() + 1).padStart(2, "0");
  const d = String(now.getUTCDate()).padStart(2, "0");
  const safeName = sanitizeFilename(filename);
  const randomId = crypto.randomUUID();

  return `uploads/${y}/${m}/${d}/${randomId}-${safeName}`;
}

function createR2Client(): S3Client {
  const accountId = assertEnv("VITE_R2_ACCOUNT_ID");
  const accessKeyId = assertEnv("VITE_R2_ACCESS_KEY_ID");
  const secretAccessKey = assertEnv("VITE_R2_SECRET_ACCESS_KEY");

  return new S3Client({
    region: "auto",
    endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
    credentials: {
      accessKeyId,
      secretAccessKey,
    },
  });
}

function toObjectUrl(objectKey: string): string | null {
  const publicBaseUrl = import.meta.env.VITE_R2_PUBLIC_BASE_URL;

  if (typeof publicBaseUrl === "string" && publicBaseUrl.trim() !== "") {
    const base = publicBaseUrl.trim().replace(/\/+$/, "");
    return `${base}/${encodeURIComponent(objectKey).replace(/%2F/g, "/")}`;
  }

  return null;
}

export async function uploadPdfDirectToR2(file: File): Promise<DirectUploadResult> {
  logUpload("start", {
    filename: file.name,
    size: file.size,
    contentType: file.type || "application/pdf",
  });

  ensurePdfFile(file);

  try {
    const bucketName = assertEnv("VITE_R2_BUCKET");
    const objectKey = createObjectKey(file.name);
    const client = createR2Client();

    logUpload("put_object_request", {
      bucket: bucketName,
      objectKey,
    });

    await client.send(
      new PutObjectCommand({
        Bucket: bucketName,
        Key: objectKey,
        Body: new Uint8Array(await file.arrayBuffer()),
        ContentType: file.type || "application/pdf",
        ContentLength: file.size,
      }),
    );

    const result = {
      objectKey,
      objectUrl: toObjectUrl(objectKey),
    };

    logUpload("success", result);
    return result;
  } catch (error) {
    logUpload("error", {
      message: error instanceof Error ? error.message : "Unknown upload error",
    });
    throw error;
  }
}

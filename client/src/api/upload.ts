import type { ExportedHandler } from "@cloudflare/workers-types";
import { AwsClient } from "aws4fetch";

interface Env {
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
  R2_ACCOUNT_ID: string;
  R2_BUCKET_NAME: string;
}

type SignBody = {
  filename?: string;
  contentType?: string;
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const body = (await request.json().catch(() => ({}))) as SignBody;
    const rawName = body.filename?.trim() || "upload.pdf";
    const safeName = rawName.replace(/[^\w.\-]/g, "_");
    const contentType = body.contentType || "application/pdf";

    const objectKey = `uploads/${crypto.randomUUID()}-${safeName}`;

    const r2 = new AwsClient({
      accessKeyId: env.R2_ACCESS_KEY_ID,
      secretAccessKey: env.R2_SECRET_ACCESS_KEY,
    });

    const url = new URL(
      `https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${env.R2_BUCKET_NAME}/${objectKey}`,
    );
    url.searchParams.set("X-Amz-Expires", "900");

    const signed = await r2.sign(
      new Request(url, {
        method: "PUT",
        headers: {
          "Content-Type": contentType,
        },
      }),
      { aws: { signQuery: true } },
    );

    return Response.json({
      uploadUrl: signed.url,
      objectKey,
      expiresIn: 900,
    });
  },
} satisfies ExportedHandler<Env>;

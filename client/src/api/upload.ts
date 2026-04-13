import type { ExportedHandler } from "@cloudflare/workers-types";
import { AwsClient } from "aws4fetch";

interface Env {
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const r2 = new AwsClient({
      accessKeyId: env.R2_ACCESS_KEY_ID,
      secretAccessKey: env.R2_SECRET_ACCESS_KEY,
    });

    // Generate a presigned PUT URL valid for 1 hour
    const url = new URL(
      "https://<ACCOUNT_ID>.r2.cloudflarestorage.com/my-bucket/image.png",
    );
    url.searchParams.set("X-Amz-Expires", "3600");

    const signed = await r2.sign(
      new Request(url, { method: "PUT" }),
      { aws: { signQuery: true } },
    );

    // Return the signed URL to the client — they can PUT directly to R2
    return Response.json({ url: signed.url });
  },
} satisfies ExportedHandler<Env>;
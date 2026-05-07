export async function track(campaignId: string, eventType: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  await fetch(`${apiUrl}/track/${campaignId}/${eventType}`, { method: "POST" });
}


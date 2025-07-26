// pages/api/leaderboard.ts
import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { SHEET_ID, GOOGLE_API_KEY } = process.env;
  if (!SHEET_ID || !GOOGLE_API_KEY) {
    return res.status(500).json({ error: "Missing env vars" });
  }

  const range = encodeURIComponent("Sheet1!A:C");  // adjust if needed
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/${range}?key=${GOOGLE_API_KEY}`;

  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error("Sheets API request failed");
    const json = await r.json();
    const rows: any[][] = json.values || [];

    const users = rows.slice(1).map(r => ({
      id:    r[0],
      name:  r[1],
      points: Number(r[2] || 0),
    })).sort((a, b) => b.points - a.points);

    res.status(200).json(users);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
}

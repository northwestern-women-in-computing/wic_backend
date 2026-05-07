// pages/api/leaderboard.ts
import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { LEAD_SHEET_ID, GOOGLE_API_KEY } = process.env;
  
  if (!LEAD_SHEET_ID || !GOOGLE_API_KEY) {
    return res.status(500).json({ error: "Missing env vars" });
  }

  const range = encodeURIComponent("Attendance!A:B"); 
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${LEAD_SHEET_ID}/values/${range}?key=${GOOGLE_API_KEY}`;

  try {
    const r = await fetch(url);
    const json = await r.json();
    const rows: string[][] = json.values || [];

    if (rows.length < 2) return res.status(200).json([]);

    const users = rows.slice(1)
      .filter(row => row[2]) // 1. Filter based on COLUMN A (Name)
      .map((row, index) => ({
        id: index, 
        name: row[1]?.trim() || "Anonymous", // 2. Map Name from COLUMN A
        points: parseInt(row[0] || "0", 10), // 3. Map Points from COLUMN B
      }));

    // The frontend handles the sorting, so we can just send the raw data
    // or keep the sort here as a backup.
    res.status(200).json(users);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
}
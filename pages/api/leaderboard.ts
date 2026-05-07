import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Use LEAD_SHEET_ID if that's what you named it in Vercel, or stay with SHEET_ID
  const { LEAD_SHEET_ID, GOOGLE_API_KEY } = process.env;
  
  if (!LEAD_SHEET_ID || !GOOGLE_API_KEY) {
    return res.status(500).json({ error: "Missing environment variables (SHEET_ID or GOOGLE_API_KEY)" });
  }

  // 1. Change 'Sheet1' to 'Attendance' to match your tab name
  const range = encodeURIComponent("Attendance!A:B"); 
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${LEAD_SHEET_ID}/values/${range}?key=${GOOGLE_API_KEY}`;

  try {
    const r = await fetch(url);
    if (!r.ok) {
        const errorData = await r.json();
        throw new Error(`Sheets API Error: ${errorData.error?.message || r.statusText}`);
    }

    const json = await r.json();
    const rows: string[][] = json.values || [];

    if (rows.length < 2) {
      return res.status(200).json([]); // Return empty list if only headers or empty
    }

    // 2. Map data and filter out rows where the name is missing
    const users = rows.slice(1)
      .filter(row => row[0]) // Only process rows that have a name
      .map((row, index) => ({
        id: index, 
        name: row[0].trim(), // Column A: Name
        points: parseInt(row[1] || "0", 10), // Column B: Points
      }))
      // 3. Apply the Points Sort + Alphabetical Tie-break
      .sort((a, b) => {
        const pointDiff = b.points - a.points;
        if (pointDiff === 0) {
          return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
        }
        return pointDiff;
      });

    res.status(200).json(users);
  } catch (e: any) {
    console.error("Leaderboard API Error:", e.message);
    res.status(500).json({ error: e.message });
  }
}
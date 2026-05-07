import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // We no longer need GOOGLE_API_KEY for this method
  const { LEAD_SHEET_ID } = process.env;
  
  if (!LEAD_SHEET_ID) {
    return res.status(500).json({ error: "Missing LEAD_SHEET_ID env var" });
  }

  // 1. Use the gviz/tq endpoint to get CSV output
  // Ensure 'Attendance' matches your tab name exactly
  const sheetName = "Attendance";
  const url = `https://docs.google.com/spreadsheets/d/${LEAD_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${sheetName}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch CSV: ${response.statusText}`);
    }

    const csvText = await response.text();
    
    // 2. Parse CSV text into rows
    // This regex handles commas inside quotes (standard for CSVs)
    const rows = csvText.split(/\r?\n/).map(line => {
      return line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).map(cell => 
        cell.replace(/^"|"$/g, '').trim()
      );
    });

    // 3. Remove header row and filter out empty rows
    const dataRows = rows.slice(1).filter(row => row.length >= 2 && row[1]);

    // 4. Map to your expected object structure
    // Since you said A=Points, B=Name:
    const users = dataRows.map((row, index) => ({
      id: index,
      name: row[1] || "Anonymous",     // Column B
      points: parseInt(row[0], 10) || 0 // Column A
    }));

    // Send the clean JSON to your frontend
    res.status(200).json(users);
  } catch (e: any) {
    console.error("CSV Leaderboard Error:", e.message);
    res.status(500).json({ error: e.message });
  }
}
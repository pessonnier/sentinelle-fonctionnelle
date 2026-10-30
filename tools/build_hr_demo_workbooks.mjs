import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = process.argv[2] ?? process.cwd();
const previewRoot = process.argv[3] ?? path.join(repoRoot, ".tmp", "hr-xlsx-preview");

const outputDir = path.join(repoRoot, "outputs", "hr-demo");
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewRoot, { recursive: true });

const palette = {
  ink: "#261443",
  violet: "#7047EB",
  pink: "#FF4FD8",
  acid: "#D8FF4F",
  cream: "#FFF8DF",
  pale: "#EEE7FF",
  white: "#FFFFFF",
  line: "#C9BFDA",
};

function styleDataSheet(sheet, usedRange, headerRange, widths) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  headerRange.format = {
    fill: palette.ink,
    font: { bold: true, color: palette.white },
    wrapText: true,
    verticalAlignment: "center",
  };
  headerRange.format.rowHeight = 34;
  usedRange.format.borders = {
    insideHorizontal: { style: "thin", color: palette.line },
    bottom: { style: "thin", color: palette.line },
  };
  usedRange.format.verticalAlignment = "center";
  widths.forEach(([column, width]) => {
    sheet.getRange(`${column}:${column}`).format.columnWidth = width;
  });
}

function addReadmeSheet(workbook, title, filename, columns) {
  const sheet = workbook.worksheets.add("Mode d'emploi");
  sheet.showGridLines = false;
  sheet.getRange("A1:F1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:F1").format = {
    fill: palette.violet,
    font: { bold: true, color: palette.white, size: 16 },
    rowHeight: 34,
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange("A3:B8").values = [
    ["Fichier", filename],
    ["Cible", "http://127.0.0.1:8000/demo/hr/login"],
    ["Usage", "Données synthétiques pour l’intégration XLSX et le test Playwright."],
    ["Sécurité", "Ne contient aucun compte réel. Ne pas réutiliser ces valeurs ailleurs."],
    ["Convention", "La première feuille est la source importable par SentinelleFonctionnelle."],
    ["Colonnes", columns],
  ];
  sheet.getRange("A3:A8").format = {
    fill: palette.acid,
    font: { bold: true, color: palette.ink },
  };
  sheet.getRange("A3:B8").format.borders = {
    preset: "outside",
    style: "thin",
    color: palette.ink,
  };
  sheet.getRange("A3:B8").format.wrapText = true;
  sheet.getRange("A:A").format.columnWidth = 22;
  sheet.getRange("B:B").format.columnWidth = 72;
  return sheet;
}

async function exportWorkbook(workbook, filename, previews) {
  const overview = await workbook.inspect({
    kind: "sheet,table",
    maxChars: 2500,
    tableMaxRows: 4,
    tableMaxCols: 16,
  });
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: `formula error scan for ${filename}`,
  });
  console.log(overview.ndjson);
  console.log(errors.ndjson);
  for (const sheetName of previews) {
    const preview = await workbook.render({
      sheetName,
      autoCrop: "all",
      scale: 1.4,
      format: "png",
    });
    await fs.writeFile(
      path.join(previewRoot, `${filename}-${sheetName.replaceAll(" ", "-")}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
  const file = await SpreadsheetFile.exportXlsx(workbook);
  await file.save(path.join(outputDir, filename));
}

const loginWorkbook = Workbook.create();
const loginSheet = loginWorkbook.worksheets.add("Connexion");
const loginRows = [
  [
    "case_id",
    "email",
    "password",
    "portal_code",
    "cosmic_charter",
    "expected_role",
    "expected_result",
  ],
  [
    "LOGIN-MANAGER-OK",
    "camille.cactus@example.test",
    "Cactus!2026",
    "CACTUS-42",
    true,
    "manager",
    "success",
  ],
  [
    "LOGIN-AGENT-OK",
    "alex.lama@example.test",
    "Lama!2026",
    "LAMA-7",
    true,
    "agent",
    "success",
  ],
  [
    "LOGIN-REFUS",
    "intrus.meteorite@example.test",
    "Erreur!2026",
    "METEO-0",
    true,
    "",
    "rejected",
  ],
];
loginSheet.getRange("A1:G4").values = loginRows;
styleDataSheet(
  loginSheet,
  loginSheet.getRange("A1:G4"),
  loginSheet.getRange("A1:G1"),
  [["A", 24], ["B", 34], ["C", 20], ["D", 18], ["E", 18], ["F", 16], ["G", 18]],
);
loginSheet.tables.add("A1:G4", true, "HrLoginCases").style = "TableStyleMedium4";
addReadmeSheet(
  loginWorkbook,
  "Jeu de connexion · Bureau des Talents Intersidéraux",
  "connexion-rh.xlsx",
  "case_id, email, password, portal_code, cosmic_charter, expected_role, expected_result",
);
await exportWorkbook(
  loginWorkbook,
  "connexion-rh.xlsx",
  ["Connexion", "Mode d'emploi"],
);

const employeeWorkbook = Workbook.create();
const employeeSheet = employeeWorkbook.worksheets.add("Collaborateurs");
const employeeRows = [
  [
    "case_id",
    "employee_number",
    "first_name",
    "last_name",
    "work_email",
    "hire_date",
    "department",
    "contract_type",
    "animal_totem",
    "favorite_color",
    "energy_level",
    "remote_days",
    "skills",
    "manager_budget",
    "manager_comment",
    "expected_title",
  ],
  [
    "EMPLOYEE-MANAGER-01",
    "EMP-NEB-042",
    "Zoé",
    "Nébuleuse",
    "zoe.nebuleuse@example.test",
    "2026-09-01",
    "Recrutement de licornes",
    "CDI intersidéral",
    "Poulpe comptable",
    "#ff4fd8",
    87,
    3,
    "Python, négociation avec les dragons",
    42000,
    "Installer un hamac ergonomique homologué.",
    "Zoé Nébuleuse",
  ],
  [
    "EMPLOYEE-AGENT-01",
    "EMP-LUN-007",
    "Sam",
    "Lunaire",
    "sam.lunaire@example.test",
    "2026-10-12",
    "Paie quantique",
    "CDD lunaire",
    "Capybara fiscaliste",
    "#48d6ff",
    64,
    2,
    "Excel, médiation interplanétaire",
    null,
    "",
    "Sam Lunaire",
  ],
  [
    "EMPLOYEE-MANAGER-02",
    "EMP-COM-314",
    "Iris",
    "Comète",
    "iris.comete@example.test",
    "2026-11-03",
    "Astrologie salariale",
    "CDI intersidéral",
    "Axolotl prévisionniste",
    "#d8ff4f",
    72,
    4,
    "TypeScript, cartographie des trous de ver",
    31500,
    "Prévoir une chaise qui pivote dans deux dimensions.",
    "Iris Comète",
  ],
];
employeeSheet.getRange("A1:P4").values = employeeRows;
styleDataSheet(
  employeeSheet,
  employeeSheet.getRange("A1:P4"),
  employeeSheet.getRange("A1:P1"),
  [
    ["A", 24], ["B", 21], ["C", 15], ["D", 18], ["E", 34], ["F", 16],
    ["G", 29], ["H", 21], ["I", 24], ["J", 18], ["K", 16], ["L", 16],
    ["M", 42], ["N", 18], ["O", 48], ["P", 22],
  ],
);
employeeSheet.getRange("K2:L4").format.numberFormat = "0";
employeeSheet.getRange("N2:N4").format.numberFormat = "#,##0";
employeeSheet.tables.add("A1:P4", true, "HrEmployeeCases").style = "TableStyleMedium4";
addReadmeSheet(
  employeeWorkbook,
  "Saisie · Collaborateurs intersidéraux",
  "saisie-collaborateurs.xlsx",
  "Une colonne par champ du formulaire et expected_title pour la consultation.",
);
await exportWorkbook(
  employeeWorkbook,
  "saisie-collaborateurs.xlsx",
  ["Collaborateurs", "Mode d'emploi"],
);

console.log(JSON.stringify({ outputDir, previewRoot }));

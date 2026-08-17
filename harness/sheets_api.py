import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List
from harness.google_auth import get_google_access_token
from harness.models import KnowledgeMap, EngineeringOutputs, Project

class GoogleSheetsClient:
    """
    Client for interacting with Google Drive & Google Sheets REST APIs.
    Uses OAuth access tokens from google_token.json.
    """

    def __init__(self):
        pass

    def _get_headers(self) -> Dict[str, str]:
        token = get_google_access_token()
        if not token:
            raise RuntimeError("No valid Google access token available. Run test_google_auth.py to authenticate.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_or_create_workspace_folder(self, folder_name: str = "Harness Workspace") -> str:
        """
        Finds or creates the Harness Workspace folder in Google Drive.
        Returns the folder ID.
        """
        headers = self._get_headers()
        # Search for existing folder
        q = urllib.parse.quote(f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            files = data.get("files", [])
            if files:
                return files[0]["id"]

        # Create folder if not found
        create_url = "https://www.googleapis.com/drive/v3/files"
        payload = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        create_req = urllib.request.Request(
            create_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(create_req) as resp:
            folder_data = json.loads(resp.read().decode("utf-8"))
            return folder_data["id"]

    def get_or_create_spreadsheet(self, title: str, folder_id: Optional[str] = None, tab_names: Optional[List[str]] = None) -> str:
        """
        Finds or creates a Google Sheet by title inside the workspace folder.
        Returns the spreadsheet ID.
        """
        headers = self._get_headers()
        q = urllib.parse.quote(f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false")
        url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            files = data.get("files", [])
            if files:
                return files[0]["id"]

        # Create new spreadsheet
        sheets_payload: List[Dict[str, Any]] = []
        tabs = tab_names or ["Sheet1"]
        for tab in tabs:
            sheets_payload.append({"properties": {"title": tab}})

        create_url = "https://sheets.googleapis.com/v4/spreadsheets"
        payload = {
            "properties": {"title": title},
            "sheets": sheets_payload
        }
        create_req = urllib.request.Request(
            create_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(create_req) as resp:
            sheet_data = json.loads(resp.read().decode("utf-8"))
            sheet_id = sheet_data["spreadsheetId"]

        # Move into folder if folder_id is specified
        if folder_id:
            try:
                move_url = f"https://www.googleapis.com/drive/v3/files/{sheet_id}?addParents={folder_id}&fields=id,parents"
                move_req = urllib.request.Request(move_url, data=b"", headers=headers, method="PATCH")
                with urllib.request.urlopen(move_req):
                    pass
            except Exception:
                pass

        return sheet_id

    def update_tab_values(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> None:
        """
        Overwrites or writes values to a specific tab range in Google Sheets.
        """
        headers = self._get_headers()
        encoded_range = urllib.parse.quote(range_name)
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}?valueInputOption=USER_ENTERED"
        payload = {"values": values}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )
        with urllib.request.urlopen(req) as resp:
            resp.read()

    def sync_project_to_sheet(self, project: Project, kmap: KnowledgeMap, outputs: Optional[EngineeringOutputs] = None) -> str:
        """
        Syncs an entire project's KnowledgeMap into its dedicated Google Sheet tabs.
        Returns the web URL to the Google Sheet.
        """
        folder_id = self.get_or_create_workspace_folder("Harness Workspace")
        sheet_title = f"Harness: {project.name}"
        tabs = ["Actors", "Goals", "Entities", "Constraints", "Outputs"]
        sheet_id = self.get_or_create_spreadsheet(sheet_title, folder_id=folder_id, tab_names=tabs)

        # 1. Sync Actors Tab
        actors_data = [["ID", "Name", "Role", "Description", "Source Doc", "Extracted At"]]
        for a in kmap.actors.values():
            actors_data.append([a.id, a.name, a.role, a.description, a.source_doc, a.extracted_at])
        self.update_tab_values(sheet_id, "Actors!A1:F50", actors_data)

        # 2. Sync Goals Tab (JTBD)
        goals_data = [["ID", "Description", "Actors", "Entities", "When (Situation)", "Why (Motivation)", "So That (Outcome)", "Failure Modes", "Source Doc"]]
        for g in kmap.goals.values():
            goals_data.append([
                g.id,
                g.description,
                ", ".join(g.actor_ids),
                ", ".join(g.entity_ids),
                g.situation_trigger or "",
                g.underlying_motivation or "",
                g.desired_outcome or "",
                "; ".join(g.failure_modes),
                g.source_doc
            ])
        self.update_tab_values(sheet_id, "Goals!A1:I50", goals_data)

        # 3. Sync Entities Tab
        entities_data = [["ID", "Name", "Fields", "Description", "Source Doc"]]
        for e in kmap.entities.values():
            entities_data.append([e.id, e.name, ", ".join(e.fields), e.description, e.source_doc])
        self.update_tab_values(sheet_id, "Entities!A1:E50", entities_data)

        # 4. Sync Constraints Tab
        constraints_data = [["ID", "Description", "Target ID", "Is Measurable", "SLA Metric", "Source Doc"]]
        for c in kmap.constraints.values():
            constraints_data.append([c.id, c.description, c.target_id or "", str(c.is_measurable), c.sla_metric or "", c.source_doc])
        self.update_tab_values(sheet_id, "Constraints!A1:F50", constraints_data)

        # 5. Sync Outputs Tab if available
        if outputs:
            outputs_data = [
                ["Generated At", "Requirements Count", "JTBD Matrix Rows", "Specification Markdown"],
                [project.last_updated, str(len(outputs.requirements)), str(len(outputs.jtbd_matrix)), outputs.spec]
            ]
            self.update_tab_values(sheet_id, "Outputs!A1:D10", outputs_data)

        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

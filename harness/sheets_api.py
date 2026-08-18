import json
import time
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from harness.google_auth import get_google_access_token
from harness.models import KnowledgeMap, EngineeringOutputs, Project

class GoogleSheetsClient:
    """
    Client for interacting with Google Drive & Google Sheets REST APIs.
    Uses OAuth access tokens from google_token.json with automatic retry logic.
    """

    def __init__(self):
        pass

    def _get_headers(self) -> Dict[str, str]:
        token = get_google_access_token()
        if not token:
            raise RuntimeError("No valid Google access token available. Run tests/test_google_auth.py to authenticate.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _execute_request(self, req: urllib.request.Request, retries: int = 3) -> Dict[str, Any]:
        """Executes a urllib request with exponential backoff retries for transient 500/503 errors."""
        last_err = None
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in [500, 502, 503, 504, 429] and attempt < retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    time.sleep(1.0)
                    continue
                raise
        raise last_err or RuntimeError("Request failed after retries.")

    def get_or_create_workspace_folder(self, folder_name: str = "Harness Workspace") -> str:
        """
        Finds or creates the Harness Workspace folder in Google Drive.
        Returns the folder ID.
        """
        headers = self._get_headers()
        q = urllib.parse.quote(f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)"
        req = urllib.request.Request(url, headers=headers)
        data = self._execute_request(req)
        files = data.get("files", [])
        if files:
            return files[0]["id"]

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
        folder_data = self._execute_request(create_req)
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
        data = self._execute_request(req)
        files = data.get("files", [])
        if files:
            sheet_id = files[0]["id"]
            if tab_names:
                self._ensure_tabs_exist(sheet_id, tab_names)
            return sheet_id

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
        sheet_data = self._execute_request(create_req)
        sheet_id = sheet_data["spreadsheetId"]

        # Move into folder if folder_id is specified
        if folder_id:
            try:
                move_url = f"https://www.googleapis.com/drive/v3/files/{sheet_id}?addParents={folder_id}&fields=id,parents"
                move_req = urllib.request.Request(move_url, data=b"", headers=headers, method="PATCH")
                self._execute_request(move_req)
            except Exception:
                pass

        # Make link shareable
        try:
            perm_url = f"https://www.googleapis.com/drive/v3/files/{sheet_id}/permissions"
            perm_req = urllib.request.Request(
                perm_url,
                data=json.dumps({"role": "writer", "type": "anyone"}).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            self._execute_request(perm_req)
        except Exception:
            pass

        return sheet_id

    def _ensure_tabs_exist(self, spreadsheet_id: str, tab_names: List[str]) -> None:
        """
        Ensures that required tabs exist in an existing spreadsheet, creating them if missing.
        """
        headers = self._get_headers()
        req = urllib.request.Request(f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}", headers=headers)
        data = self._execute_request(req)
        existing_tabs = {s["properties"]["title"] for s in data.get("sheets", [])}

        missing = [t for t in tab_names if t not in existing_tabs]
        if not missing:
            return

        requests = [{"addSheet": {"properties": {"title": t}}} for t in missing]
        batch_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"
        batch_payload = {"requests": requests}
        batch_req = urllib.request.Request(
            batch_url,
            data=json.dumps(batch_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        self._execute_request(batch_req)

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
        self._execute_request(req)

    def sync_project_to_sheet(
        self,
        project: Project,
        kmap: KnowledgeMap,
        outputs: Optional[EngineeringOutputs] = None,
        source_doc_url: str = ""
    ) -> str:
        """
        Syncs an entire project's KnowledgeMap and transcripts history into its dedicated Google Sheet tabs.
        Returns the web URL to the Google Sheet.
        """
        folder_id = self.get_or_create_workspace_folder("Harness Workspace")
        sheet_title = f"Harness: {project.name}"
        tabs = ["Transcripts", "Actors", "Goals", "Entities", "Constraints", "Outputs"]
        sheet_id = self.get_or_create_spreadsheet(sheet_title, folder_id=folder_id, tab_names=tabs)

        # 1. Sync Transcripts Log Tab
        all_sources = set()
        if source_doc_url:
            all_sources.add(source_doc_url)
        for a in kmap.actors.values():
            if a.source_doc:
                all_sources.add(a.source_doc)
        for g in kmap.goals.values():
            if g.source_doc:
                all_sources.add(g.source_doc)

        transcripts_data = [["#", "Transcript Doc URL", "Status", "Ingested At", "Total Actors", "Total Goals", "Total Entities"]]
        for idx, src in enumerate(sorted(all_sources), 1):
            transcripts_data.append([
                str(idx),
                src,
                "Synthesized & Complete",
                project.last_updated,
                str(len(kmap.actors)),
                str(len(kmap.goals)),
                str(len(kmap.entities))
            ])
        self.update_tab_values(sheet_id, "Transcripts!A1:G20", transcripts_data)

        # 2. Sync Actors Tab
        actors_data = [["ID", "Name", "Role", "Description", "Source Doc", "Extracted At"]]
        for a in kmap.actors.values():
            actors_data.append([a.id, a.name, a.role, a.description, a.source_doc, a.extracted_at])
        self.update_tab_values(sheet_id, "Actors!A1:F50", actors_data)

        # 3. Sync Goals Tab (JTBD)
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

        # 4. Sync Entities Tab
        entities_data = [["ID", "Name", "Fields", "Description", "Source Doc"]]
        for e in kmap.entities.values():
            entities_data.append([e.id, e.name, ", ".join(e.fields), e.description, e.source_doc])
        self.update_tab_values(sheet_id, "Entities!A1:E50", entities_data)

        # 5. Sync Constraints Tab
        constraints_data = [["ID", "Description", "Target ID", "Is Measurable", "SLA Metric", "Source Doc"]]
        for c in kmap.constraints.values():
            constraints_data.append([c.id, c.description, c.target_id or "", str(c.is_measurable), c.sla_metric or "", c.source_doc])
        self.update_tab_values(sheet_id, "Constraints!A1:F50", constraints_data)

        # 6. Sync Outputs Tab if available
        if outputs:
            outputs_data = [
                ["Generated At", "Requirements Count", "JTBD Matrix Rows", "Specification Markdown"],
                [project.last_updated, str(len(outputs.requirements)), str(len(outputs.jtbd_matrix)), outputs.spec]
            ]
            self.update_tab_values(sheet_id, "Outputs!A1:D10", outputs_data)

        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

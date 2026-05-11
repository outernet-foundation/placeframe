import os
from pathlib import Path

ASSET_PATH = Path("apps/MakeItSing/Assets/_LocalWorkspace/Resources/UnityEnv.asset")
SCRIPT_GUID = "063f3dae153481b49a1b37b39d133309"


def main() -> None:
    supabase_project_id = os.environ["SUPABASE_PROJECT_ID"]
    supabase_api_key = os.environ["SUPABASE_API_KEY"]
    photon_project_id = os.environ["PHOTON_PROJECT_ID"]

    ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    ASSET_PATH.write_text(
        f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {SCRIPT_GUID}, type: 3}}
  m_Name: UnityEnv
  m_EditorClassIdentifier:
  supabaseProjectId: {supabase_project_id}
  supabaseApiKey: {supabase_api_key}
  runInOfflineMode: 0
  overridePlatform: 0
  platform: 0
  overrideConfig: 1
  logGroups: -1
  logLevel: 0
  stackTraceLevel: 0
  notificationLogLevel: 0
  photonProjectId: {photon_project_id}
  loginAutomatically: 0
  domain:
  username:
  password:
  room:
  disableSystemUI: 0
"""
    )

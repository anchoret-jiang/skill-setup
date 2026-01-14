import os
import shutil
import zipfile
import re
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Claude Code 目录路径
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_PLUGINS_DIR = CLAUDE_DIR / "plugins"
CLAUDE_SKILL_DIR = CLAUDE_PLUGINS_DIR / "marketplaces" / "anthropic-agent-skills"
CLAUDE_CACHE_DIR = CLAUDE_PLUGINS_DIR / "cache" / "anthropic-agent-skills"
INSTALLED_PLUGINS_FILE = CLAUDE_PLUGINS_DIR / "installed_plugins.json"

# 临时上传目录
TEMP_DIR = Path("./temp_uploads")

# 确保目录存在
TEMP_DIR.mkdir(exist_ok=True)
CLAUDE_SKILL_DIR.mkdir(parents=True, exist_ok=True)
CLAUDE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SkillInfo(BaseModel):
    id: str  # Unique identifier (folder name or file path hash)
    name: str
    description: str
    path: str
    isValid: bool
    isInstalled: bool = False

class InstallRequest(BaseModel):
    paths: List[str]

def parse_skill_metadata(skill_path: Path) -> Optional[SkillInfo]:
    """
    Parses a skill directory or file to extract metadata.
    Expects a SKILL.md file.
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding="utf-8")
        # Simple regex to parse frontmatter-like content or first few lines
        name_match = re.search(r"name:\s*(.+)", content, re.IGNORECASE)
        desc_match = re.search(r"description:\s*(.+)", content, re.IGNORECASE)
        
        name = name_match.group(1).strip() if name_match else skill_path.name
        description = desc_match.group(1).strip() if desc_match else "No description found."
        
        return SkillInfo(
            id=skill_path.name,
            name=name,
            description=description,
            path=str(skill_path.absolute()),
            isValid=True
        )
    except Exception as e:
        print(f"Error parsing {skill_path}: {e}")
        return None

def extract_zip(zip_path: Path, extract_to: Path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def load_installed_plugins() -> dict:
    """加载 installed_plugins.json"""
    if INSTALLED_PLUGINS_FILE.exists():
        try:
            return json.loads(INSTALLED_PLUGINS_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {"version": 2, "plugins": {}}

def save_installed_plugins(data: dict):
    """保存 installed_plugins.json"""
    INSTALLED_PLUGINS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def register_skill(skill_name: str, cache_path: Path):
    """将技能注册到 installed_plugins.json"""
    data = load_installed_plugins()
    key = f"{skill_name}@anthropic-agent-skills"
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    data["plugins"][key] = [{
        "scope": "user",
        "installPath": str(cache_path),
        "version": "unknown",
        "installedAt": now,
        "lastUpdated": now,
        "isLocal": True
    }]
    save_installed_plugins(data)

def unregister_skill(skill_name: str):
    """从 installed_plugins.json 移除技能"""
    data = load_installed_plugins()
    key = f"{skill_name}@anthropic-agent-skills"
    if key in data["plugins"]:
        del data["plugins"][key]
        save_installed_plugins(data)

@app.post("/upload", response_model=List[SkillInfo])
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_skills = []
    
    # Clear temp dir for clean slate (optional, but good for demo)
    # shutil.rmtree(TEMP_DIR)
    # TEMP_DIR.mkdir()

    for file in files:
        temp_file_path = TEMP_DIR / file.filename
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # If zip, extract
        if file.filename.endswith(".zip"):
            extract_folder = TEMP_DIR / file.filename[:-4]
            extract_folder.mkdir(exist_ok=True)
            try:
                extract_zip(temp_file_path, extract_folder)
                # Search for skills inside extracted folder
                # It could be the folder itself or subfolders
                # BFS/DFS to find SKILL.md
                found_any = False
                for root, dirs, _ in os.walk(extract_folder):
                    path = Path(root)
                    if (path / "SKILL.md").exists():
                        skill = parse_skill_metadata(path)
                        if skill:
                            uploaded_skills.append(skill)
                            found_any = True
                
                if not found_any:
                    # Maybe the zip didn't contain SKILL.md directly? 
                    # For now just ignore if not found
                    pass
            except Exception as e:
                print(f"Error extracting zip: {e}")
        else:
            # If it's a folder upload (drag and drop folder usually comes as multiple files, 
            # handling that is complex in web. Let's assume zip or individual SKILL.md handling if needed)
            # For this MVP, we focus on Zip files mainly as "drag folder" in web usually requires 
            # webkitdirectory and recursive upload handling which is complex.
            # But if a single file SKILL.md is uploaded?
            pass

    return uploaded_skills

@app.post("/install")
async def install_skills(req: InstallRequest):
    installed = []
    for source_path_str in req.paths:
        source_path = Path(source_path_str)
        if not source_path.exists():
            continue

        skill_name = source_path.name

        # 1. 复制到技能市场目录
        skill_target = CLAUDE_SKILL_DIR / skill_name
        if skill_target.exists():
            shutil.rmtree(skill_target)
        shutil.copytree(source_path, skill_target)

        # 2. 复制到缓存目录
        cache_target = CLAUDE_CACHE_DIR / skill_name / "unknown"
        cache_target.parent.mkdir(parents=True, exist_ok=True)
        if cache_target.exists():
            shutil.rmtree(cache_target)
        shutil.copytree(source_path, cache_target)

        # 3. 注册到 installed_plugins.json
        register_skill(skill_name, cache_target)

        installed.append(skill_name)

    return {"status": "success", "installed": installed}

def find_skills_in_path(base_path: Path) -> List[dict]:
    """递归查找路径下的所有 SKILL.md 文件"""
    skills = []
    if not base_path.exists():
        return skills

    for skill_md in base_path.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        try:
            content = skill_md.read_text(encoding="utf-8")
            name_match = re.search(r"name:\s*(.+)", content, re.IGNORECASE)
            desc_match = re.search(r"description:\s*(.+)", content, re.IGNORECASE)

            name = name_match.group(1).strip() if name_match else skill_dir.name
            description = desc_match.group(1).strip() if desc_match else "No description"

            skills.append({
                "name": name,
                "description": description,
                "path": str(skill_dir),
                "id": skill_dir.name
            })
        except:
            pass
    return skills

@app.get("/installed", response_model=List[SkillInfo])
async def list_installed():
    """列出所有已安装的技能（从 installed_plugins.json 读取）"""
    skills = []
    installed_data = load_installed_plugins()

    for plugin_key, plugin_info_list in installed_data.get("plugins", {}).items():
        if not plugin_info_list:
            continue

        plugin_info = plugin_info_list[0]  # 取第一个
        install_path = Path(plugin_info.get("installPath", ""))

        if not install_path.exists():
            continue

        # 解析插件名和来源
        parts = plugin_key.split("@")
        plugin_name = parts[0] if parts else plugin_key
        source = parts[1] if len(parts) > 1 else "unknown"

        # 查找该路径下的所有技能
        found_skills = find_skills_in_path(install_path)

        if found_skills:
            for skill_data in found_skills:
                skills.append(SkillInfo(
                    id=f"{plugin_key}::{skill_data['id']}",
                    name=skill_data["name"],
                    description=skill_data["description"],
                    path=skill_data["path"],
                    isValid=True,
                    isInstalled=True
                ))
        else:
            # 如果没找到 SKILL.md，显示插件本身
            skills.append(SkillInfo(
                id=plugin_key,
                name=plugin_name,
                description=f"Plugin from {source}",
                path=str(install_path),
                isValid=True,
                isInstalled=True
            ))

    return skills

@app.delete("/installed/{skill_id:path}")
async def uninstall_skill(skill_id: str):
    """卸载技能"""
    # 解析 skill_id，格式可能是 "plugin_key::skill_name" 或 "plugin_key"
    if "::" in skill_id:
        plugin_key, _ = skill_id.split("::", 1)
    else:
        plugin_key = skill_id

    # 解析插件名和来源
    parts = plugin_key.split("@")
    plugin_name = parts[0] if parts else plugin_key
    source = parts[1] if len(parts) > 1 else ""

    # 只允许卸载通过本工具安装的技能（anthropic-agent-skills）
    if source and source != "anthropic-agent-skills":
        raise HTTPException(
            status_code=403,
            detail=f"无法卸载来自 {source} 的技能，请使用 Claude Code 的插件管理功能"
        )

    found = False

    # 1. 删除技能市场目录
    skill_path = CLAUDE_SKILL_DIR / plugin_name
    if skill_path.exists():
        shutil.rmtree(skill_path)
        found = True

    # 2. 删除缓存目录
    cache_path = CLAUDE_CACHE_DIR / plugin_name
    if cache_path.exists():
        shutil.rmtree(cache_path)
        found = True

    # 3. 从注册文件移除
    unregister_skill(plugin_name)

    if found:
        return {"status": "success", "message": f"已卸载 {plugin_name}"}

    raise HTTPException(status_code=404, detail="技能未找到")

@app.get("/config")
async def get_config():
    """获取配置信息"""
    return {
        "skillDir": str(CLAUDE_SKILL_DIR),
        "cacheDir": str(CLAUDE_CACHE_DIR),
        "pluginsFile": str(INSTALLED_PLUGINS_FILE)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

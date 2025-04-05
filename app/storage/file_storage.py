import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class FileStorage:
    def __init__(self, base_dir: str = "data/memories"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> str:
        """
        Save a memory to a local JSON file.
        
        Args:
            memory_id: The ID of the memory
            memory_data: The memory data to save
            
        Returns:
            The path to the saved file
        """
        # Create a directory for the user if it doesn't exist
        user_dir = self.base_dir / memory_data["user_id"]
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the file path
        file_path = user_dir / f"{memory_id}.json"
        
        # Add timestamp if not present
        if "saved_at" not in memory_data:
            memory_data["saved_at"] = datetime.now().isoformat()
        
        # Create a copy of memory_data without the embedding property
        memory_data_to_save = memory_data.copy()
        if "embedding" in memory_data_to_save:
            del memory_data_to_save["embedding"]
        
        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory_data_to_save, f, ensure_ascii=False, indent=2)
        
        return str(file_path)

    def get_memory(self, memory_id: str, user_id: str) -> Dict[str, Any]:
        """
        Retrieve a memory from a local JSON file.
        
        Args:
            memory_id: The ID of the memory
            user_id: The ID of the user
            
        Returns:
            The memory data
        """
        file_path = self.base_dir / user_id / f"{memory_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Memory file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """
        删除指定记忆的本地文件
        
        Args:
            memory_id: 要删除的记忆ID
            user_id: 记忆所属的用户ID
            
        Returns:
            如果删除成功返回True
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        file_path = self.base_dir / user_id / f"{memory_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Memory file not found: {file_path}")
            
        os.remove(file_path)
        return True
from typing import List
from fastapi import Depends, HTTPException
from app.models.user import User
from app.api.deps import get_current_active_user

class RoleChecker:
    def __init__(self, allowed_permissions: List[str]):
        self.allowed_permissions = allowed_permissions

    def __call__(self, user: User = Depends(get_current_active_user)):
        # For naive implementation without loading full relations, we assume
        # Super Admin has role_id = 1.
        if user.role_id == 1:
            return True
            
        # In a real implementation, you'd iterate over user.role.permissions
        # and check if any match `self.allowed_permissions`.
        user_permissions = [] # user.role.permissions -> [p.key for p in permissions]
        
        for permission in self.allowed_permissions:
            if permission in user_permissions:
                return True
                
        raise HTTPException(status_code=403, detail="Operation not permitted")

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_current_user
from app.db.database import get_db

SessionDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[object, Depends(get_current_active_user)]

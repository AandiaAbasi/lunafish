import os
import uuid


def upload_to_dynamic(instance, filename):
    from .models import About, Article, Banner
    from account.models import User
    """Dynamic upload path for user images"""
    name, ext = os.path.splitext(filename)
    filename = f"{uuid.uuid4().hex}{ext}"
    folder = "users"
    if isinstance(instance, About):  
        folder = "about"
    elif isinstance(instance, Article): 
        folder = "articles"
    elif isinstance(instance, Banner):
        folder = "banners"
    elif isinstance(instance, User):
        folder = "users"
    else:
        folder = "others"
    
    return os.path.join(folder, filename)

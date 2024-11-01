# from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
# from ..import schemas, models, helper_functions, authorization
# from ..database import get_db
# from sqlalchemy.orm import Session


# router = APIRouter(
#     prefix="/stylists",
#     tags=['Stylists']
# )

# @router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=schemas.StylistCreateResponse)
# def signup(stylist: schemas.StylistCreate, db: Session = Depends(get_db)):
#     """Creates a new stylist account"""
    
#     try:
#         # Check if a user with the same username or email already exists
#         existing_stylist = db.query(models.Stylist).filter(
#             (models.Stylist.username == stylist.username) | (models.Stylist.email == stylist.email)
#         ).first()

#         if existing_stylist:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Stylist with this username or email already exists"
#             )

#         # Hash the password
#         hashed_password = helper_functions.hash_password(stylist.password)

#         # Prepare data to exclude fields not meant to be directly user-controlled (like 'role')
#         stylist_data = stylist.dict(exclude_unset=True, exclude={"role"})
#         stylist_data["password"] = hashed_password  

#         # Create a new user instance with the filtered data
#         new_stylist = models.User(**stylist_data)
#         db.add(new_stylist)
#         db.commit()
#         db.refresh(new_stylist)

#         return new_stylist

#     except Exception as e:
#         # Log the exception if using logging for better debugging
#         print(f"An error occurred during signup: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while creating the stylist. Please try again later."
#         )
    

# @router.get("/profile/{stylist_id}", response_model=schemas.StylistCreateResponse)
# def get_user_profile(stylist_id: int, db: Session = Depends(get_db), 
#                      current_user: int = Depends(authorization.get_current_user)):
    
#     """Stylists retrieving a specific stylist's info"""
#     stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
#     if not stylist:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
#                             detail=f"user with id: {stylist_id} does not exist")
#     return stylist



# @router.put("/profile/update/{stylist_id}", response_model=schemas.StylistCreateResponse)
# def update_user_profile(stylist_id: int, updated_profile: schemas.StylistCreate, 
#                         db: Session = Depends(get_db), current_user: int = Depends(authorization.get_current_user)):
    
#     """Updates a stylist's profile info"""
#     stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()

#     if stylist == None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"The requested stylist profile does not exist")
    
#     if stylist.id != current_user.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Can not perform the requested action, Unauthorized access")
    
#     for key, value in updated_profile.dict(exclude_unset=True).items():
#         setattr(stylist, key, value)

#     db.commit()
#     return stylist



# @router.delete("/profile/delete/{stylist_id}", status_code=status.HTTP_404_NOT_FOUND)
# def delete_user_profile(stylist_id: int, db: Session = Depends(get_db), 
#                         current_user: int = Depends(authorization.get_current_user)):
#     """Deletes a stylists's account"""
#     stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()

#     if stylist is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"The requested stylist profile does not exist")
    
#     if stylist.id != current_user.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Cannot perform the requested action, Unauthorized access")
    
#     db.delete(stylist)
#     db.commit()
    
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


# @router.put("/profile/change_password/{stylist_id}", response_model=schemas.StylistCreateResponse)
# def updated_stylist_password(stylist_id: int, password_change: schemas.PasswordChange, 
#                           db: Session = Depends(get_db), current_user: int = Depends(authorization.get_current_user)):
#     """Updates a user's password"""
#     stylist = db.query(models.Stylist).filter(models.Stylist.id == current_user.id).first()

#     if not stylist:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
#                             detail="Stylist not found")
#     if stylist.id != stylist_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Cannot perform the requested action, Unauthorized access")
#     # Verify old password
#     if not helper_functions.verify_password(password_change.old_password, stylist.password):
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Old password is incorrect")
    
#     # Hash and update the new password
#     stylist.password = helper_functions.hash_password(password_change.new_password)
#     db.commit()



# @router.get("/dashboard/{stylist_id}", response_model=schemas.StylistDashboardResponse, 
#             status_code=status.HTTP_200_OK)
# def stylist_dashboard(stylist_id: int, db: Session = Depends(get_db), 
#                       current_user: int = Depends(authorization.get_current_user)):
#     """Retrieves Stylists dashboard"""
#     stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()

#     if stylist is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"The requested stylist profile does not exist")
    
#     if stylist.id != current_user.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Cannot perform the requested action, Unauthorized access")
#     profile = stylist
#     appointments = db.query(models.Appointment).filter(models.Appointment.stylist_id == stylist_id).all()
#     services = db.query(models.Service).filter(models.Service.stylist_id == stylist_id).all()

    
#     return schemas.StylistDashboardResponse(
#         profile=profile,
#         appointments=appointments,
#         services=services
#     )
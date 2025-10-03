# Profile and Settings Pages

This document describes the user profile and settings functionality in SupaQuery.

## Features

### Profile Page (`/profile`)

The profile page allows users to view and edit their account information.

#### Features:
- **View Profile Information**
  - Username (read-only)
  - Full name (editable)
  - Email address (editable)
  - Account ID (read-only)
  - Member since date (read-only)
  - User roles and permissions

- **Edit Profile**
  - Click "Edit Profile" button to enable editing
  - Update full name and email
  - Changes are saved to the database
  - Success/error notifications with toast messages

- **Activity Summary**
  - Number of documents uploaded
  - Number of queries made
  - Number of documents shared
  - (Currently displays 0 - will be populated with real data)

#### Implementation:
- **Frontend**: `/frontend/src/app/profile/page.tsx`
- **Backend**: 
  - GET `/api/users/me` - Fetch current user info
  - PUT `/api/users/me` - Update user profile

### Settings Page (`/settings`)

The settings page provides comprehensive account management with four tabs.

#### Tabs:

##### 1. Account Settings
- View username (read-only)
- View email (links to profile for editing)
- View account type/roles
- Delete account option (coming soon)

##### 2. Security Settings
- **Change Password**
  - Enter current password
  - Enter new password (min 8 characters)
  - Confirm new password
  - Toggle password visibility with eye icon
  - Backend validates current password before updating
  
- **Two-Factor Authentication**
  - Coming soon

##### 3. Notifications Settings
- Email notifications toggle
- Document sharing alerts toggle
- Save preferences button

##### 4. Preferences Settings
- Auto-save toggle
- Theme selection (Light/Dark/System)
- Save preferences button

#### Implementation:
- **Frontend**: `/frontend/src/app/settings/page.tsx`
- **Backend**:
  - POST `/api/users/change-password` - Change user password

## Backend API Endpoints

### Update User Profile
```http
PUT /api/users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-01T12:00:00",
  "updated_at": "2025-10-03T14:30:00",
  "roles": ["user"]
}
```

### Change Password
```http
POST /api/users/change-password
Authorization: Bearer {token}
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Current password is incorrect
- `400 Bad Request` - New password too short/long (8-72 characters)
- `500 Internal Server Error` - Failed to update password

## Database Changes

### New Methods in `postgres.py`:

#### `update_user(user_id, **kwargs)`
- Updates user profile fields (full_name, email)
- Validates email uniqueness
- Returns updated User object with roles loaded

#### `update_user_password(user_id, hashed_password)`
- Updates user password
- Takes pre-hashed password (bcrypt)
- Returns boolean success status

## Usage

### Accessing the Pages

1. **Login** to your account
2. **Click your avatar** in the top-right corner
3. Select:
   - **Profile** - to view/edit your profile
   - **Settings** - to manage account settings and change password

### Protected Routes

Both profile and settings pages are protected routes that:
- Redirect to login if not authenticated
- Show loading spinner during authentication check
- Only render content when user is authenticated

### Navigation

- Both pages have a back button (←) in the top-left to return home
- UserMenu dropdown provides quick access from anywhere

## Security Features

### Password Requirements
- Minimum 8 characters
- Maximum 72 characters (bcrypt limitation)
- Must provide current password to change
- Passwords are hashed with bcrypt before storage

### Authentication
- All endpoints require JWT token authentication
- Token must be valid and not expired
- User can only update their own profile

### Validation
- Email uniqueness is validated
- Email format is validated (EmailStr from Pydantic)
- Current password is verified before password change
- All errors are caught and returned with appropriate status codes

## UI Components Used

From shadcn/ui:
- `Card` - Container for sections
- `Input` - Text input fields
- `Button` - Action buttons
- `Switch` - Toggle controls
- `Tabs` - Tabbed interface
- `Badge` - Role indicators
- `Avatar` - User avatar display
- `Label` - Form labels
- `Separator` - Section dividers
- `Toast` - Success/error notifications

Icons from lucide-react:
- `ArrowLeft` - Back navigation
- `User`, `Mail`, `Calendar`, `Shield` - Information icons
- `Lock`, `Bell`, `Palette` - Tab icons
- `Eye`, `EyeOff` - Password visibility toggle
- `Save` - Save action

## Future Enhancements

### Profile Page
- Upload profile picture
- View real activity statistics
- Export user data
- Account deletion with confirmation

### Settings Page
- Two-factor authentication setup
- Session management (view active sessions)
- API key generation
- Connected services/integrations
- Privacy settings
- Data export/import

### Backend
- Activity tracking for statistics
- Email verification for email changes
- Password reset via email
- Account deletion with data cleanup
- Audit log for security events

## Testing

### Manual Testing Steps

1. **Profile Update**:
   - Login as test user
   - Navigate to /profile
   - Click "Edit Profile"
   - Change full name and email
   - Click "Save Changes"
   - Verify toast notification
   - Refresh page and verify changes persist

2. **Password Change**:
   - Navigate to /settings
   - Go to "Security" tab
   - Enter current password
   - Enter new password (twice)
   - Click "Change Password"
   - Verify success toast
   - Logout and login with new password

3. **Error Handling**:
   - Try changing to an email that's already taken
   - Try changing password with wrong current password
   - Try password less than 8 characters
   - Verify appropriate error messages

## Code Structure

```
frontend/src/app/
  ├── profile/
  │   └── page.tsx          # Profile page component
  ├── settings/
  │   └── page.tsx          # Settings page component
  └── layout.tsx            # Already includes Toaster

backend/
  ├── main.py               # API endpoints
  │   ├── PUT /api/users/me
  │   └── POST /api/users/change-password
  └── app/database/
      └── postgres.py       # Database methods
          ├── update_user()
          └── update_user_password()
```

## Dependencies

All required dependencies are already installed:
- Frontend: React, Next.js, shadcn/ui, lucide-react
- Backend: FastAPI, SQLAlchemy, asyncpg, bcrypt, pydantic

No new dependencies required! ✨


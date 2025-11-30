# Troubleshooting Guide - Ape Wellness Tracker

## Issue: New Users See No Apes

### Symptoms
- New user registers successfully
- User can log in
- Dashboard shows no apes
- "All Apes" page is empty

### Root Cause Analysis
The system is designed so that **all logged-in users can see all apes** (global ape population). If new users see no apes, the issue is likely:

1. **No apes exist in the database**
2. **All apes are archived**
3. **Database connection issues**
4. **Browser cache issues**

### Solution Steps

#### Step 1: Check Current System Status
```bash
python test_user_access.py
```
This will show you:
- All users and their roles
- How many apes each user can see
- Total apes in the database

#### Step 2: Ensure Apes Exist
```bash
python sync_apes_for_user.py ensure
```
This will create the standard 6 apes if they don't exist.

#### Step 3: Verify Ape Population
```bash
python sync_apes_for_user.py list
```
This will show all apes and their status.

#### Step 4: Check User Roles
```bash
python manage_roles.py list
```
This will show all users and their assigned roles.

### Expected Results
After running the above commands, you should see:
- **6 active apes**: MAISHA, TECO, NYOTA, CLARA, MALI, ELIKYA
- **All users can see all apes** (regardless of roles)
- **Admin users have Admin role**

## Issue: Users Can't Delete Apes

### Symptoms
- User tries to delete an ape
- Gets "Access Denied" or "Forbidden" error
- Delete button doesn't appear

### Root Cause
Only users with the "Admin" role can delete apes permanently.

### Solution
Assign Admin role to the user:
```bash
python manage_roles.py assign user@email.com Admin
```

### Verify Admin Access
```bash
python manage_roles.py list
```
Look for `Roles: ['Admin']` next to the user's email.

## Issue: New User Registration Problems

### Symptoms
- Registration form doesn't work
- User can't log in after registration
- Database errors during registration

### Solution
1. **Ensure database is initialized**:
   ```bash
   python init_db.py
   ```

2. **Set up the complete system**:
   ```bash
   python setup_system.py
   ```

3. **Create user manually if needed**:
   ```bash
   python manage_roles.py create-user user@email.com password123
   ```

## Issue: Browser Shows Old Data

### Symptoms
- Changes don't appear in browser
- Still seeing old ape data
- Login issues

### Solution
1. **Clear browser cache**
2. **Use incognito/private window**
3. **Hard refresh** (Ctrl+F5 or Cmd+Shift+R)
4. **Check if you're on the right URL**

## System Architecture

### Ape Visibility
- **All apes are GLOBAL** - shared across all users
- **No role restrictions** on viewing apes
- **All logged-in users** can see all active apes

### Role-Based Access
- **Admin**: Can delete apes, manage categories, edit recipes
- **Researcher**: Can view and log feeding data
- **Viewer**: Can view data only
- **No Role**: Can view and log feeding data (default)

### Database Structure
- **Apes table**: Global ape population
- **Meals table**: User-specific meal entries (tracked by user_id)
- **Users table**: User accounts and roles

## Quick Fixes

### Reset Everything
```bash
python setup_system.py
```

### Create Admin User
```bash
python create_admin.py
```

### Ensure Apes Exist
```bash
python sync_apes_for_user.py ensure
```

### Check System Status
```bash
python test_user_access.py
```

## Common Commands

### User Management
```bash
# List all users and roles
python manage_roles.py list

# Create new user
python manage_roles.py create-user user@email.com password123

# Create admin user
python manage_roles.py create-user admin@email.com password123 admin

# Assign role to user
python manage_roles.py assign user@email.com Admin
```

### Ape Management
```bash
# List all apes
python sync_apes_for_user.py list

# Ensure standard apes exist
python sync_apes_for_user.py ensure

# Test user access
python test_user_access.py
```

## Still Having Issues?

1. **Check the logs** when running the application
2. **Verify database file exists** in the `instance/` directory
3. **Try creating a fresh database**:
   ```bash
   rm instance/database.db
   python setup_system.py
   ```
4. **Check file permissions** on the database file
5. **Verify Python environment** and dependencies

## Expected Behavior

### New User Registration
1. User registers with email/password
2. User can immediately log in
3. User sees all 6 standard apes on dashboard
4. User can log feeding sessions for any ape
5. User's meal entries are tracked with their user ID

### Admin Functions
1. Only Admin users can delete apes permanently
2. Only Admin users can manage food categories
3. Only Admin users can edit/delete recipes and meals
4. All users can view apes and log feeding sessions

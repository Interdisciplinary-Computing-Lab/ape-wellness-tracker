# Role Management & Ape Synchronization Guide

## Overview

The Ape Wellness Tracker uses a role-based access control system where:
- **Apes are GLOBAL** - All users see the same ape population
- **Meals are USER-SPECIFIC** - Each user's meal entries are tracked separately
- **Admin-only functions** - Only admins can delete apes, manage categories, etc.

## Quick Setup

### 1. Initial System Setup
```bash
python setup_system.py
```
This will:
- Create standard roles (Admin, Researcher, Viewer)
- Set up the standard ape population (MAISHA, TECO, NYOTA, CLARA, MALI, ELIKYA)
- Create an admin user if none exists
- Display system status

### 2. Create Admin User
```bash
python create_admin.py
```

### 3. Create Regular User
```bash
python create_user.py
```

## Role Management

### List Users and Roles
```bash
python manage_roles.py list
```

### Create New Role
```bash
python manage_roles.py create-role "Researcher" "Can view and log data"
```

### Assign Role to User
```bash
python manage_roles.py assign researcher@ape.org Admin
```

### Remove Role from User
```bash
python manage_roles.py remove researcher@ape.org Admin
```

### Create User with Role
```bash
python manage_roles.py create-user researcher@ape.org password123 admin
```

## Ape Management

### Ensure Standard Apes Exist
```bash
python sync_apes_for_user.py ensure
```

### Sync Apes for All Users
```bash
python sync_apes_for_user.py sync
```

### Sync Apes for Specific User
```bash
python sync_apes_for_user.py sync researcher@ape.org
```

### List Ape Access
```bash
python sync_apes_for_user.py list
```

## Current Admin-Only Functions

These functions require the "Admin" role:
- **Delete apes** (permanent deletion from database)
- **Edit/delete recipes**
- **Edit/delete meals**

## Functions Available to All Users

These functions are available to all logged-in users:
- **View and manage food categories**
- **Add/edit/delete food categories**
- **View all apes and log feeding sessions**
- **Access all food items and recipes**

## Standard Roles

### Admin
- Full access to all features
- Can delete apes permanently
- Can edit/delete any meal or recipe
- Can manage all food categories

### Researcher
- Can view all apes
- Can log feeding sessions
- Can view all meal data
- Can manage food categories
- Cannot delete apes permanently

### Viewer
- Can view all apes
- Can view meal data
- Can manage food categories
- Cannot log feeding sessions
- Cannot delete anything

## Ape Population

The system automatically ensures these standard apes exist:
- **MAISHA** (Age: 24, Weight: 42.5kg, Mother: Matata)
- **TECO** (Age: 14, Weight: 38.2kg)
- **NYOTA** (Age: 26, Weight: 45.8kg)
- **CLARA** (Age: 14, Weight: 39.1kg)
- **MALI** (Age: 17, Weight: 41.3kg)
- **ELIKYA** (Age: 27, Weight: 44.7kg, Mother: Matata)

## New User Registration

When new users register:
1. They automatically see all apes (global population)
2. They can log meals for any ape
3. Their meal entries are tracked with their user ID
4. Standard apes are automatically created if missing

## Best Practices

1. **Always have at least one admin user**
2. **Use the setup script for initial deployment**
3. **Assign appropriate roles based on user responsibilities**
4. **Regular users should not have admin privileges**
5. **Use archive instead of delete for apes when possible**

## Troubleshooting

### No Admin Users
```bash
python create_admin.py
```

### Missing Apes
```bash
python sync_apes_for_user.py ensure
```

### User Can't Access Features
```bash
python manage_roles.py list
python manage_roles.py assign user@email.com Admin
```

### Reset System
```bash
python setup_system.py
```

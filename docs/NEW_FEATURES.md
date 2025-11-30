# New Features - Ape Wellness Tracker

This document describes the new HTML pages and features that have been added to the Ape Wellness Tracker application based on the provided wireframes.

## Overview

The application now includes two new main pages:
1. **Ape Profile Page** - Individual ape profile with nutrition tracking and notes
2. **Log Feeding Page** - Interface for logging feeding events for multiple apes

## New Pages

### 1. Ape Profile Page (`/ape_profile`)

**File:** `backend/templates/ape_profile.html`

**Features:**
- **Profile Card**: Displays ape image, name, age, weight, and status buttons (BAR, GA, NBM)
- **Nutrition Section**: Shows today's calories with a pie chart and detailed nutrition table
- **Notes/Observations**: Form for adding notes with status updates and display of recent notes
- **Swelling Tracker**: Slider input (0-3) for recording swelling levels
- **Responsive Design**: Mobile-friendly layout with Bootstrap 5

**Key Components:**
- Interactive pie chart using Chart.js
- Real-time swelling level display
- Note posting with timestamps
- Status button updates
- Hover effects and animations

### 2. Log Feeding Page (`/log_feeding`)

**File:** `backend/templates/log_feeding.html`

**Features:**
- **Active Apes Selection**: Horizontal scrollable list of ape avatars for multi-selection
- **Quick Add Buttons**: One-click food items (banana, cabbage, carrot, egg)
- **Add Food Form**: Dropdown selection with quantity and calories inputs
- **Current Feeding Table**: Dynamic table with food items, calories, quantities, and delete buttons
- **Save/Clear Functions**: Save feeding data or clear all items

**Key Components:**
- Multi-ape selection with visual feedback
- Quick add functionality with animations
- Dynamic table management
- Form validation and error handling
- Success animations and alerts

## Styling and CSS

### Ape Profile CSS (`backend/static/css/ape_profile.css`)
- Custom styling for profile cards and status buttons
- Pie chart container styling
- Notes section with hover effects
- Swelling slider with color-coded levels
- Mobile responsive design
- Custom animations and transitions

### Log Feeding CSS (`backend/static/css/log_feeding.css`)
- Ape avatar selection styling
- Quick add button animations
- Form input styling with increment/decrement buttons
- Table styling with hover effects
- Mobile responsive design
- Custom scrollbars and animations

## JavaScript Functionality

### Ape Profile JS (`backend/static/js/ape_profile.js`)
- **Pie Chart**: Interactive nutrition visualization using Chart.js
- **Swelling Slider**: Real-time level display with color coding
- **Notes System**: Add notes with timestamps and user attribution
- **Status Updates**: Dynamic status button management
- **Alert System**: User feedback for actions

### Log Feeding JS (`backend/static/js/log_feeding.js`)
- **Ape Selection**: Toggle selection with visual feedback
- **Quick Add**: One-click food addition to feeding table
- **Form Handling**: Validation and auto-population of calories
- **Table Management**: Add, remove, and clear feeding items
- **Data Collection**: Gather selected apes and feeding data for saving

## Updated Components

### Base Template (`backend/templates/base.html`)
- Added Bootstrap 5 and Font Awesome
- Responsive navigation with dropdown menu
- User authentication display
- Consistent styling across all pages

### Dashboard (`backend/templates/index.html`)
- Complete Bootstrap redesign
- Card-based layout for forms and tables
- Data overview statistics
- Improved table styling with actions
- Mobile responsive design

## Routes Added

### New Flask Routes (`backend/routes/main.py`)
```python
@site.route('/ape_profile')
@login_required
def ape_profile():
    """Display the ape profile page with nutrition data and notes."""

@site.route('/log_feeding')
@login_required
def log_feeding():
    """Display the log feeding page for adding nutrition data."""
```

## Technical Features

### Responsive Design
- Mobile-first approach with Bootstrap 5
- Responsive tables and forms
- Adaptive navigation
- Touch-friendly interface elements

### Interactive Elements
- Hover effects on buttons and cards
- Smooth animations and transitions
- Real-time feedback for user actions
- Loading states and success animations

### Data Management
- Form validation and error handling
- Dynamic table updates
- Data collection for backend integration
- User feedback and confirmation dialogs

### Accessibility
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader friendly

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Responsive design for all screen sizes
- Progressive enhancement approach

## Future Enhancements

1. **Backend Integration**: Connect forms to actual database operations
2. **Real-time Updates**: WebSocket integration for live data updates
3. **Image Upload**: Support for ape profile photos
4. **Advanced Charts**: More detailed nutrition analytics
5. **Export Features**: PDF reports and data export
6. **User Permissions**: Role-based access control
7. **Search and Filter**: Advanced data filtering capabilities

## File Structure

```
backend/
├── templates/
│   ├── ape_profile.html      # New ape profile page
│   ├── log_feeding.html      # New feeding log page
│   ├── base.html             # Updated base template
│   └── index.html            # Updated dashboard
├── static/
│   ├── css/
│   │   ├── ape_profile.css   # Profile page styles
│   │   └── log_feeding.css   # Feeding page styles
│   ├── js/
│   │   ├── ape_profile.js    # Profile page functionality
│   │   └── log_feeding.js    # Feeding page functionality
│   └── images/
│       └── bonobo-placeholder.jpg  # Placeholder image
└── routes/
    └── main.py               # Updated with new routes
```

## Usage Instructions

1. **Accessing New Pages**: Use the navigation menu to access "Ape Profile" and "Log Feeding"
2. **Ape Profile**: View individual ape data, add notes, and track swelling levels
3. **Log Feeding**: Select multiple apes, add food items, and save feeding data
4. **Responsive Design**: All pages work on desktop, tablet, and mobile devices

The new features provide a modern, user-friendly interface for managing ape wellness data with intuitive interactions and comprehensive functionality. 
# Apache Superset Setup for Ape Wellness Tracker

## Overview
Apache Superset is a modern, enterprise-ready business intelligence web application that provides fast, lightweight, and intuitive analytics. This guide will help you set up Superset to create advanced analytics dashboards for the Ape Wellness Tracker.

## Installation Options

### Option 1: Docker (Recommended)
```bash
# Create a directory for Superset
mkdir superset
cd superset

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  superset:
    image: apache/superset:latest
    container_name: superset
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=your-secret-key-here
      - SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py
    volumes:
      - ./superset_config.py:/app/pythonpath/superset_config.py
      - superset_home:/app/superset_home
    depends_on:
      - db
    command: ["/app/docker/docker-init.sh"]

  db:
    image: postgres:13
    container_name: superset_db
    environment:
      - POSTGRES_DB=superset
      - POSTGRES_USER=superset
      - POSTGRES_PASSWORD=superset
    volumes:
      - superset_db_data:/var/lib/postgresql/data

volumes:
  superset_home:
  superset_db_data:
EOF

# Create Superset configuration
cat > superset_config.py << 'EOF'
import os
from datetime import timedelta

# Superset specific config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Flask App Builder configuration
APP_NAME = "Ape Wellness Analytics"
APP_ICON = "/static/assets/images/superset-logo-horiz.png"
FAVICONS = [{"href": "/static/assets/images/favicon.png"}]

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
# Add endpoints that need to be exempt from CSRF protection
WTF_CSRF_EXEMPT_LIST = []
# A CSRF token that expires in 1 year
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

# Flask-Caching configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': 'redis',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 1,
    'CACHE_REDIS_URL': 'redis://redis:6379/1'
}

# Database configuration
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://superset:superset@db:5432/superset'

# Redis configuration
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_CELERY_DB = 0
REDIS_RESULTS_DB = 1

# Celery configuration
class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = ("superset.sql_lab", "superset.tasks")
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
    }

CELERY_CONFIG = CeleryConfig

# Feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "VERSIONED_EXPORT": True,
    "DASHBOARD_FILTERS_EXPERIMENTAL": True,
}

# Security configuration
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "your-secret-key-here")

# Custom security manager
CUSTOM_SECURITY_MANAGER = None

# Custom CSS for branding
CUSTOM_CSS = """
.navbar-brand {
    font-weight: bold;
    color: #2E86AB !important;
}
"""

# Custom JavaScript
CUSTOM_JS = """
// Custom JavaScript for Ape Wellness Tracker
console.log('Ape Wellness Analytics loaded');
"""
EOF

# Start Superset
docker-compose up -d

# Initialize Superset
docker exec -it superset superset-init
```

### Option 2: Local Installation
```bash
# Install Python dependencies
pip install apache-superset

# Initialize database
superset db upgrade

# Create admin user
superset fab create-admin

# Load example data (optional)
superset load_examples

# Initialize
superset init

# Start server
superset run -p 8088 --with-threads --reload --debugger
```

## Database Connection Setup

### 1. Connect to Ape Wellness Tracker Database
In Superset, go to **Data > Databases** and add a new database:

**Connection String:**
```
sqlite:////path/to/your/ape-wellness-tracker/instance/ape_wellness.db
```

**For PostgreSQL (if migrated):**
```
postgresql://username:password@localhost:5432/ape_wellness
```

### 2. Create Dataset
Go to **Data > Datasets** and create a new dataset with the following SQL:

```sql
-- Ape Wellness Analytics Dataset
SELECT 
    a.ape_name,
    a.birthday,
    a.weight,
    a.mother,
    m.date as meal_date,
    r.meal_name,
    r.food_category,
    r.calories,
    r.description,
    strftime('%Y-%m', m.date) as month,
    strftime('%Y', m.date) as year,
    strftime('%W', m.date) as week_of_year
FROM apes a
LEFT JOIN meals m ON a.id = m.ape_id
LEFT JOIN recipe r ON m.recipe_id = r.id
WHERE m.date IS NOT NULL
ORDER BY m.date DESC
```

## Recommended Dashboards

### 1. Ape Nutrition Overview Dashboard
**Charts to include:**
- **Total Calories by Ape** (Bar Chart)
- **Food Category Distribution** (Pie Chart)
- **Monthly Calorie Trends** (Line Chart)
- **Average Calories per Meal** (Metric Chart)
- **Recent Feeding Activity** (Table)

### 2. Long-term Health Trends Dashboard
**Charts to include:**
- **Weight Trends Over Time** (Line Chart)
- **Calorie Intake vs Age** (Scatter Plot)
- **Seasonal Feeding Patterns** (Heatmap)
- **Food Category Preferences** (Sunburst Chart)
- **Feeding Frequency Analysis** (Histogram)

### 3. Comparative Analytics Dashboard
**Charts to include:**
- **Ape Comparison Matrix** (Table)
- **Nutritional Balance Score** (Gauge Chart)
- **Growth Rate Analysis** (Area Chart)
- **Dietary Diversity Index** (Bar Chart)
- **Health Score Trends** (Line Chart)

## Chart Configurations

### 1. Food Category Distribution Pie Chart
```json
{
  "metrics": ["SUM(calories)"],
  "groupby": ["food_category"],
  "color_scheme": "supersetColors",
  "show_labels": true,
  "show_legend": true
}
```

### 2. Monthly Calorie Trends Line Chart
```json
{
  "metrics": ["SUM(calories)"],
  "groupby": ["month"],
  "temporal_columns_lookup": {
    "month": true
  },
  "color_scheme": "supersetColors",
  "show_legend": true,
  "x_axis_time_format": "%Y-%m"
}
```

### 3. Ape Comparison Bar Chart
```json
{
  "metrics": ["SUM(calories)", "COUNT(meal_name)"],
  "groupby": ["ape_name"],
  "color_scheme": "supersetColors",
  "show_legend": true,
  "orientation": "horizontal"
}
```

## Advanced Analytics Features

### 1. Custom Metrics
Create custom metrics for advanced analysis:

**Nutritional Balance Score:**
```sql
CASE 
  WHEN SUM(CASE WHEN food_category = 'Fruits' THEN calories ELSE 0 END) > 0 
   AND SUM(CASE WHEN food_category = 'Vegetables' THEN calories ELSE 0 END) > 0
   AND SUM(CASE WHEN food_category = 'Protein' THEN calories ELSE 0 END) > 0
  THEN 100
  ELSE 50
END
```

**Dietary Diversity Index:**
```sql
COUNT(DISTINCT food_category) * 20
```

### 2. Time-based Analysis
**Weekly Patterns:**
```sql
strftime('%W', meal_date) as week_number,
strftime('%Y', meal_date) as year
```

**Seasonal Analysis:**
```sql
CASE 
  WHEN strftime('%m', meal_date) IN ('12', '01', '02') THEN 'Winter'
  WHEN strftime('%m', meal_date) IN ('03', '04', '05') THEN 'Spring'
  WHEN strftime('%m', meal_date) IN ('06', '07', '08') THEN 'Summer'
  ELSE 'Fall'
END as season
```

## Integration with Flask App

### 1. API Endpoint for Superset
Add this route to your Flask app:

```python
@site.route('/api/analytics/<int:ape_id>')
@login_required
def get_analytics_data(ape_id):
    """Get analytics data for Superset integration"""
    ape = Apes.query.get_or_404(ape_id)
    
    # Get comprehensive analytics data
    analytics_data = {
        'ape_info': {
            'id': ape.id,
            'name': ape.ape_name,
            'age': ape.age,
            'weight': ape.weight,
            'mother': ape.mother
        },
        'nutrition_summary': {
            'total_meals': len(ape.meals),
            'total_calories': sum(meal.recipe.calories for meal in ape.meals),
            'avg_calories_per_meal': sum(meal.recipe.calories for meal in ape.meals) / len(ape.meals) if ape.meals else 0
        },
        'category_breakdown': {},
        'monthly_trends': []
    }
    
    return jsonify(analytics_data)
```

### 2. Embed Superset Dashboard
Add this to your ape profile template:

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">
            <i class="fas fa-chart-line mr-1"></i>
            Advanced Analytics
        </h3>
    </div>
    <div class="card-body">
        <iframe 
            src="http://localhost:8088/superset/dashboard/1/"
            width="100%" 
            height="600px" 
            frameborder="0">
        </iframe>
    </div>
</div>
```

## Security Considerations

### 1. Authentication
- Use Superset's built-in authentication
- Configure LDAP/AD integration for enterprise environments
- Set up role-based access control (RBAC)

### 2. Data Access
- Limit database access to read-only for analytics
- Use database views for sensitive data
- Implement row-level security if needed

### 3. Network Security
- Use HTTPS in production
- Configure firewall rules
- Use reverse proxy (nginx) for additional security

## Performance Optimization

### 1. Database Optimization
- Create indexes on frequently queried columns
- Use materialized views for complex aggregations
- Partition large tables by date

### 2. Caching
- Enable Redis caching for query results
- Use Superset's built-in caching features
- Implement application-level caching

### 3. Query Optimization
- Use efficient SQL queries
- Limit result sets with pagination
- Use async queries for long-running operations

## Monitoring and Maintenance

### 1. Health Checks
- Monitor Superset application health
- Set up database connection monitoring
- Track query performance metrics

### 2. Backup Strategy
- Regular database backups
- Superset configuration backups
- Dashboard and chart exports

### 3. Updates
- Keep Superset updated
- Monitor security patches
- Test updates in staging environment

## Troubleshooting

### Common Issues:
1. **Database Connection Errors**: Check connection strings and credentials
2. **Chart Rendering Issues**: Verify data types and null values
3. **Performance Problems**: Optimize queries and enable caching
4. **Authentication Issues**: Check user permissions and roles

### Logs:
- Superset logs: `/app/superset_home/logs/`
- Database logs: Check your database system logs
- Application logs: Use your logging framework

## Next Steps

1. **Set up the basic Superset installation**
2. **Connect to your Ape Wellness Tracker database**
3. **Create the recommended dashboards**
4. **Integrate with your Flask application**
5. **Configure security and performance optimizations**
6. **Train users on dashboard usage**

This setup will provide comprehensive analytics capabilities for your Ape Wellness Tracker, enabling data-driven insights into ape nutrition and health trends. 
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            filterByCategory(category, this);
        });
    });
});

// Category filter function
function filterByCategory(category, clickedButton) {
    const categoryItems = document.querySelectorAll('.category-item');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    // Update active button
    filterButtons.forEach(btn => btn.classList.remove('active'));
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
    
    // Filter items
    categoryItems.forEach(item => {
        if (category === 'all' || item.dataset.category === category) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

// Add event listeners for edit and delete buttons
document.addEventListener('DOMContentLoaded', function() {
    // Edit category buttons
    document.querySelectorAll('.edit-category-btn').forEach(button => {
        button.addEventListener('click', function() {
            const categoryId = this.getAttribute('data-id');
            const categoryName = this.getAttribute('data-name');
            const categoryDescription = this.getAttribute('data-description');
            const categoryIcon = this.getAttribute('data-icon');
            
            // Populate the edit form
            document.getElementById('editCategoryName').value = categoryName;
            document.getElementById('editCategoryDescription').value = categoryDescription || '';
            document.getElementById('editCategoryIcon').value = categoryIcon || 'fas fa-tag';
            
            // Set the form action
            document.getElementById('editCategoryForm').action = `/categories/${categoryId}/edit`;
            
            // Show the modal
            $('#editCategoryModal').modal('show');
        });
    });
    
    // Delete category buttons
    document.querySelectorAll('.delete-category-btn').forEach(button => {
        button.addEventListener('click', function() {
            const categoryId = this.getAttribute('data-id');
            const categoryName = this.getAttribute('data-name');
            
            // Set the category name in the confirmation modal
            document.getElementById('deleteCategoryName').textContent = categoryName;
            
            // Set the form action
            document.getElementById('deleteCategoryForm').action = `/categories/${categoryId}/delete`;
            
            // Show the confirmation modal
            $('#deleteCategoryModal').modal('show');
        });
    });
});

// Show notification function
function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
